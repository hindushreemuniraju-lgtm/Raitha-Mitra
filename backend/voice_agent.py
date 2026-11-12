"""
Standalone LiveKit Agents Worker for Raitha Mitra using Sarvam AI Saaras (STT),
Bulbul (TTS), and Sarvam LLM with instant STT-based interruption (barge-in).

Run alongside FastAPI when LiveKit + Sarvam credentials are configured:
    python voice_agent.py dev
"""

import json
import logging

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("raitha_mitra.voice_worker")


def run_worker() -> None:
    try:
        from livekit.agents import Agent, AgentSession, JobContext, WorkerOptions, cli  # type: ignore
        from livekit.plugins import sarvam  # type: ignore
    except ImportError as exc:
        raise RuntimeError(
            "livekit-agents[sarvam] is required to run voice_agent.py. "
            "Install with: pip install \"livekit-agents[sarvam]>=1.8.6,<2\""
        ) from exc

    async def entrypoint(ctx: JobContext):
        await ctx.connect()
        participant = await ctx.wait_for_participant()

        language_code = "kn-IN"
        context_payload = {}
        if participant.metadata:
            try:
                parsed = json.loads(participant.metadata)
                language_code = parsed.get("language_code", "kn-IN")
                context_payload = parsed.get("context", {})
            except ValueError:
                pass

        instructions = (
            "You are Raitha Mitra ('Your Smart Farming Companion'). "
            f"Reply strictly in language {language_code}. Never switch to English unexpectedly. "
            "Never re-ask for crop or location if already present in the farmer context below. "
            "If disease diagnosis is asked without a photo scan, instruct the farmer to upload a photo first.\n"
            f"Farmer Context: {json.dumps(context_payload, ensure_ascii=False)}"
        )

        agent = Agent(
            instructions=instructions,
            stt=sarvam.STT(
                language=language_code,
                model="saaras:v3-realtime",
                mode="transcribe",
            ),
            llm=sarvam.LLM(model="sarvam-105b"),
            tts=sarvam.TTS(
                target_language_code=language_code,
                model="bulbul:v4-flash",
                speaker="anushka" if language_code != "hi-IN" else "anant",
            ),
        )

        # vad=None lets Sarvam Saaras manage server-side VAD and immediate barge-in interruption
        session = AgentSession(
            vad=None,
            turn_handling={
                "turn_detection": "stt",
                "endpointing": {"min_delay": 0.07},
            },
        )
        await session.start(agent=agent, room=ctx.room)
        await session.generate_reply()

    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))


if __name__ == "__main__":
    run_worker()
