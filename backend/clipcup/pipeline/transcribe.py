"""
Clip Cup Pipeline - Step 2: Speech-to-Text Transcription via AssemblyAI.
Extracts word-level timestamps and speaker utterances.
"""

import logging
import os
from pathlib import Path
from typing import Dict, List, Any

logger = logging.getLogger("clipcup.pipeline.transcribe")


def transcribe_audio(
    audio_path: Path,
    job_id: str = "default",
    api_key: str = None,
    allow_mock: bool = True,
) -> Dict[str, Any]:
    """
    Transcribes audio using AssemblyAI SDK with word timestamps and speaker utterances.
    Falls back to a structured synthetic transcript if API key is not configured
    and allow_mock is True.
    """
    extra = {"job_id": job_id}
    api_key = api_key or os.getenv("ASSEMBLYAI_API_KEY", "").strip()

    if not api_key:
        if allow_mock or os.getenv("ALLOW_MOCK_FALLBACK", "True").lower() in ("true", "1"):
            logger.warning(
                "ASSEMBLYAI_API_KEY is not set. Generating synthetic test transcript for local execution.",
                extra=extra,
            )
            return _generate_mock_transcript(audio_path, job_id=job_id)
        else:
            raise ValueError(
                "ASSEMBLYAI_API_KEY environment variable is required for speech transcription."
            )

    logger.info("Initializing AssemblyAI transcription...", extra=extra)
    try:
        import assemblyai as aai

        aai.settings.api_key = api_key

        config = aai.TranscriptionConfig(
            speaker_labels=True,
            punctuate=True,
            format_text=True,
        )

        transcriber = aai.Transcriber()
        transcript = transcriber.transcribe(str(audio_path), config=config)

        if transcript.status == aai.TranscriptStatus.error:
            raise RuntimeError(f"AssemblyAI transcription error: {transcript.error}")

        utterances: List[Dict[str, Any]] = []
        if transcript.utterances:
            for u in transcript.utterances:
                utterances.append({
                    "speaker": getattr(u, "speaker", "A"),
                    "text": u.text,
                    "start_ms": int(u.start),
                    "end_ms": int(u.end),
                })
        else:
            duration_ms = int((transcript.audio_duration or 10.0) * 1000)
            utterances.append({
                "speaker": "A",
                "text": transcript.text or "",
                "start_ms": 0,
                "end_ms": duration_ms,
            })

        words: List[Dict[str, Any]] = []
        if transcript.words:
            for w in transcript.words:
                words.append({
                    "word": w.text,
                    "start_ms": int(w.start),
                    "end_ms": int(w.end),
                    "confidence": float(getattr(w, "confidence", 1.0) or 1.0),
                })

        logger.info(
            f"Transcription succeeded: {len(utterances)} utterances, {len(words)} words.",
            extra=extra,
        )

        return {
            "text": transcript.text or "",
            "utterances": utterances,
            "words": words,
            "audio_duration_seconds": float(transcript.audio_duration or 0.0),
        }

    except Exception as e:
        logger.error(f"AssemblyAI transcription failed: {e}", extra=extra)
        if allow_mock:
            logger.warning(
                f"Falling back to synthetic transcript due to AssemblyAI exception: {e}",
                extra=extra,
            )
            return _generate_mock_transcript(audio_path, job_id=job_id)
        raise


def _generate_mock_transcript(audio_path: Path, job_id: str) -> Dict[str, Any]:
    """
    Synthesizes a realistic transcript with word timestamps for offline/local development.
    """
    import wave

    duration_s = 30.0
    try:
        with wave.open(str(audio_path), "rb") as wf:
            frames = wf.getnframes()
            rate = wf.getframerate()
            if rate > 0:
                duration_s = frames / float(rate)
    except Exception:
        pass

    duration_ms = int(duration_s * 1000)
    sample_text = (
        "Welcome to Clip Cup. This is an automated highlight extracted from your source video. "
        "In this video we demonstrate how computer vision and AI language models can collaborate "
        "to automatically detect engaging moments, track speakers, and generate vertical shorts."
    )
    words_list = sample_text.split()
    total_words = len(words_list)
    word_interval_ms = max(200, duration_ms // max(total_words, 1))

    words = []
    current_ms = 0
    for w in words_list:
        end_ms = min(current_ms + word_interval_ms - 50, duration_ms)
        words.append({
            "word": w,
            "start_ms": current_ms,
            "end_ms": end_ms,
            "confidence": 0.98,
        })
        current_ms = min(current_ms + word_interval_ms, duration_ms)

    utterances = [
        {
            "speaker": "Speaker 1",
            "text": sample_text,
            "start_ms": 0,
            "end_ms": duration_ms,
        }
    ]

    return {
        "text": sample_text,
        "utterances": utterances,
        "words": words,
        "audio_duration_seconds": duration_s,
    }
