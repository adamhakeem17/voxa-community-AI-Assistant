import os
from dotenv import load_dotenv

from pipecat.frames.frames import LLMRunFrame
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.worker import PipelineParams, PipelineWorker
from pipecat.processors.aggregators.llm_context import LLMContext
from pipecat.processors.aggregators.llm_response_universal import LLMContextAggregatorPair
from pipecat.runner.types import RunnerArguments
from pipecat.runner.utils import create_transport
from pipecat.services.google.gemini_live.llm import GeminiLiveLLMService
from pipecat.transports.base_transport import BaseTransport, TransportParams
from pipecat.workers.runner import WorkerRunner

from voxa.prompt import SYSTEM_PROMPT
from voxa.tools import (
    lookup_business_fact,
    check_demo_availability,
    create_demo_reservation,
    create_group_enquiry,
    allergy_safety_check,
)

load_dotenv(override=True)

transport_params = {
    "webrtc": lambda: TransportParams(
        audio_in_enabled=True,
        audio_out_enabled=True,
    ),
}

TOOLS = [
    lookup_business_fact,
    check_demo_availability,
    create_demo_reservation,
    create_group_enquiry,
    allergy_safety_check,
]


async def run_bot(transport: BaseTransport, runner_args: RunnerArguments):
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError(
            "GOOGLE_API_KEY is missing. Copy .env.example to .env and add your Gemini API key."
        )

    llm = GeminiLiveLLMService(
        api_key=api_key,
        settings=GeminiLiveLLMService.Settings(
            model=os.getenv(
                "GEMINI_LIVE_MODEL",
                "models/gemini-3.1-flash-live-preview",
            ),
            voice=os.getenv("VOXA_VOICE", "Charon"),
            system_instruction=SYSTEM_PROMPT,
            max_tokens=700,
        ),
    )

    context = LLMContext(
        [{"role": "developer", "content": "Greet the caller now."}],
        TOOLS,
    )
    user_aggregator, assistant_aggregator = LLMContextAggregatorPair(context)

    pipeline = Pipeline(
        [
            transport.input(),
            user_aggregator,
            llm,
            transport.output(),
            assistant_aggregator,
        ]
    )

    worker = PipelineWorker(
        pipeline,
        params=PipelineParams(
            enable_metrics=True,
            enable_usage_metrics=True,
        ),
        idle_timeout_secs=runner_args.pipeline_idle_timeout_secs,
    )

    runner = WorkerRunner(handle_sigint=runner_args.handle_sigint)
    await runner.add_workers(worker)

    @transport.event_handler("on_client_connected")
    async def on_client_connected(transport, client):
        await worker.queue_frames([LLMRunFrame()])

    @transport.event_handler("on_client_disconnected")
    async def on_client_disconnected(transport, client):
        await runner.cancel()

    await runner.run()


async def bot(runner_args: RunnerArguments):
    transport = await create_transport(runner_args, transport_params)
    await run_bot(transport, runner_args)


if __name__ == "__main__":
    from pipecat.runner.run import main

    main()
