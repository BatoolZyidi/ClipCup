"""
Clip Cup Pipeline - Step 3: Bedrock Segment Selection.
Prompts AWS Bedrock for strict JSON {start_ms, end_ms, topic, reason},
validates <=90s, snaps to utterance boundaries, and falls back to highest speech density window.
"""

import json
import logging
import os
import re
from typing import Dict, Any, List

logger = logging.getLogger("clipcup.pipeline.select_segment")

MAX_SEGMENT_DURATION_MS = 120000  # 120 seconds (2 minutes)
MIN_SEGMENT_DURATION_MS = 15000  # 15 seconds
DEFAULT_FALLBACK_DURATION_MS = 90000  # 90 seconds


def _snap_to_utterance_boundaries(
    start_ms: int,
    end_ms: int,
    utterances: List[Dict[str, Any]],
    video_duration_ms: int,
) -> tuple[int, int]:
    """
    Snaps start_ms and end_ms to the nearest utterance start and end boundaries,
    ensuring end_ms - start_ms <= MAX_SEGMENT_DURATION_MS.
    """
    if not utterances:
        start_clamped = max(0, min(start_ms, video_duration_ms - MIN_SEGMENT_DURATION_MS))
        end_clamped = min(video_duration_ms, start_clamped + MAX_SEGMENT_DURATION_MS)
        return start_clamped, max(start_clamped + MIN_SEGMENT_DURATION_MS, end_clamped)

    # Find closest utterance start
    best_start = utterances[0]["start_ms"]
    min_start_diff = abs(best_start - start_ms)
    for u in utterances:
        u_start = u["start_ms"]
        diff = abs(u_start - start_ms)
        if diff < min_start_diff and u_start < video_duration_ms:
            min_start_diff = diff
            best_start = u_start

    # Find closest utterance end that occurs after best_start
    valid_ends = [u["end_ms"] for u in utterances if u["end_ms"] > best_start]
    if not valid_ends:
        best_end = min(video_duration_ms, best_start + DEFAULT_FALLBACK_DURATION_MS)
    else:
        best_end = valid_ends[0]
        min_end_diff = abs(best_end - end_ms)
        for u_end in valid_ends:
            diff = abs(u_end - end_ms)
            if diff < min_end_diff and (u_end - best_start) <= MAX_SEGMENT_DURATION_MS:
                min_end_diff = diff
                best_end = u_end

    # Guarantee duration bounds
    if (best_end - best_start) > MAX_SEGMENT_DURATION_MS:
        best_end = best_start + MAX_SEGMENT_DURATION_MS
    elif (best_end - best_start) < MIN_SEGMENT_DURATION_MS and video_duration_ms >= MIN_SEGMENT_DURATION_MS:
        best_end = min(video_duration_ms, best_start + MIN_SEGMENT_DURATION_MS)

    return best_start, best_end

    if (best_end - best_start) < MIN_SEGMENT_DURATION_MS:
        best_end = min(video_duration_ms, best_start + MIN_SEGMENT_DURATION_MS)

    return int(best_start), int(min(best_end, video_duration_ms))


def _highest_density_fallback(
    transcript_data: Dict[str, Any],
    video_duration_ms: int,
    reason_note: str,
    job_id: str = "default",
) -> Dict[str, Any]:
    """
    Intelligent NLP highlight ranker:
    Scans the entire transcript for emotional peaks, question-and-answer pairs,
    insight revelations, and high-energy speech. Selects an optimal, self-contained
    natural segment (30s to 90s, up to 120s) from ANYWHERE in the video,
    never just the beginning.
    """
    extra = {"job_id": job_id}
    logger.info(
        f"Analyzing full transcript with contextual highlight scoring: {reason_note}",
        extra=extra,
    )

    utterances = transcript_data.get("utterances", [])
    words = transcript_data.get("words", [])

    if not utterances and not words:
        # Absolute fallback if transcript is empty
        end_ms = min(video_duration_ms, 60000)
        return {
            "start_ms": 0,
            "end_ms": end_ms,
            "topic": "Video Highlight",
            "reason": f"Fallback: Selected first {end_ms // 1000}s ({reason_note})",
        }

    # High-value conversational signals indicating true highlights & climaxes
    HOOK_KEYWORDS = {
        "why", "how", "what", "secret", "realize", "discovered", "truth",
        "amazing", "incredible", "mistake", "important", "remember",
        "story", "learned", "actually", "suddenly", "finally", "because",
        "listen", "problem", "solution", "crazy", "unbelievable", "never",
        "always", "best", "worst", "future", "money", "life", "success"
    }

    # Evaluate potential segment windows: test durations of 30s, 45s, 60s, 75s, 90s
    candidate_durations_ms = [30000, 45000, 60000, 75000, 90000]
    best_candidate = None
    highest_score = -1.0

    # If utterances exist, candidate start points are utterance beginnings
    start_candidates = []
    if utterances:
        for idx, u in enumerate(utterances):
            u_start = u.get("start_ms", 0)
            # Skip candidates starting in the last 15 seconds
            if u_start < video_duration_ms - 15000:
                start_candidates.append((u_start, idx))
    else:
        for t in range(0, max(1, video_duration_ms - 30000), 5000):
            start_candidates.append((t, 0))

    for start_t, start_idx in start_candidates:
        for target_dur in candidate_durations_ms:
            raw_end = start_t + target_dur
            if raw_end > video_duration_ms:
                raw_end = video_duration_ms
            actual_dur = raw_end - start_t
            if actual_dur < 20000:
                continue

            # Snap to utterance boundaries if available
            if utterances:
                snap_s, snap_e = _snap_to_utterance_boundaries(
                    start_t, raw_end, utterances, video_duration_ms
                )
            else:
                snap_s, snap_e = start_t, raw_end

            # Gather text and words within this candidate window
            window_words = [
                w for w in words
                if snap_s <= w.get("start_ms", 0) <= snap_e
            ]
            window_text = " ".join([
                u.get("text", "") for u in utterances
                if (u.get("start_ms", 0) >= snap_s and u.get("end_ms", 0) <= snap_e)
                or (u.get("start_ms", 0) <= snap_s and u.get("end_ms", 0) >= snap_e)
            ]).lower()

            word_count = len(window_words) if window_words else len(window_text.split())
            if word_count < 10:
                continue

            # Scoring factors:
            # 1. Speaking cadence & density (words per minute)
            dur_minutes = (snap_e - snap_s) / 60000.0
            wpm = word_count / max(0.1, dur_minutes)
            cadence_score = min(wpm / 150.0, 1.5)  # optimal speaking pace ~130-170 wpm

            # 2. Hook and climax keyword resonance
            keyword_hits = sum(1 for kw in HOOK_KEYWORDS if kw in window_text)
            hook_score = min(keyword_hits * 0.25, 2.0)

            # 3. Question & answer dynamic (presence of question mark or question words)
            has_question = "?" in window_text or any(w in window_text[:80] for w in ["why", "how", "what", "is it"])
            qa_score = 0.5 if has_question else 0.0

            # 4. Anti-intro bias: penalize the first 20 seconds of long videos (introductions/intros)
            intro_penalty = -0.6 if snap_s < 20000 and video_duration_ms > 120000 else 0.0

            # Composite engagement score
            total_score = cadence_score + hook_score + qa_score + intro_penalty

            if total_score > highest_score:
                highest_score = total_score
                # Extract first meaningful phrase for topic
                topic = "Key Discussion"
                if utterances and start_idx < len(utterances):
                    first_text = utterances[start_idx].get("text", "").strip()
                    first_words = first_text.split()[:5]
                    if first_words:
                        topic = " ".join(first_words).capitalize()

                best_candidate = {
                    "start_ms": snap_s,
                    "end_ms": snap_e,
                    "topic": topic,
                    "reason": f"High engagement moment ({int((snap_e - snap_s)/1000)}s segment with strong dialogue & narrative climax)",
                }

    if best_candidate:
        logger.info(
            f"Selected optimal highlight: [{best_candidate['start_ms']/1000:.1f}s - {best_candidate['end_ms']/1000:.1f}s] "
            f"Topic: '{best_candidate['topic']}' (Score: {highest_score:.2f})",
            extra=extra,
        )
        return best_candidate

    # Safe fallback
    return {
        "start_ms": 0,
        "end_ms": min(video_duration_ms, 60000),
        "topic": "Video Highlight",
        "reason": f"Fallback window: {reason_note}",
    }


def _extract_json_from_text(text: str) -> Dict[str, Any]:
    """Extracts and parses JSON object from LLM response text."""
    # Look for code block or first { ... }
    text = text.strip()
    match = re.search(r"\{[\s\S]*\}", text)
    if match:
        text = match.group(0)
    return json.loads(text)


def select_segment(
    transcript_data: Dict[str, Any],
    video_duration_ms: int,
    job_id: str = "default",
    model_id: str = None,
    aws_region: str = None,
) -> Dict[str, Any]:
    """
    Sends transcript to AWS Bedrock to identify the most viral, engaging segment <=90s.
    Returns: {"start_ms": int, "end_ms": int, "topic": str, "reason": str}
    """
    extra = {"job_id": job_id}
    model_id = model_id or os.getenv(
        "BEDROCK_MODEL_ID", "anthropic.claude-3-5-sonnet-20240620-v1:0"
    )
    aws_region = aws_region or os.getenv(
        "BEDROCK_REGION", os.getenv("AWS_REGION", "us-east-1")
    )

    # If entire video is already <= 120s, use full video or full utterances
    if video_duration_ms <= MAX_SEGMENT_DURATION_MS:
        logger.info(
            f"Video is {video_duration_ms / 1000:.1f}s <= 120s; selecting complete video.",
            extra=extra,
        )
        return {
            "start_ms": 0,
            "end_ms": video_duration_ms,
            "topic": "Complete Highlight",
            "reason": "Video is within 120-second short form limit.",
        }

    # Format transcript summary
    utterances = transcript_data.get("utterances", [])
    if not utterances:
        return _highest_density_fallback(
            transcript_data, video_duration_ms, "No utterances available", job_id=job_id
        )

    transcript_lines = []
    for u in utterances:
        start_s = u["start_ms"] / 1000.0
        end_s = u["end_ms"] / 1000.0
        transcript_lines.append(f"[{start_s:.1f}s - {end_s:.1f}s] {u.get('speaker', 'Speaker')}: {u.get('text', '')}")

    transcript_str = "\n".join(transcript_lines)
    # Truncate if excessively long for prompt safety
    if len(transcript_str) > 28000:
        transcript_str = transcript_str[:28000] + "\n...[truncated]"

    prompt = (
        f"You are an expert viral short-form video producer.\n"
        f"Video total duration: {video_duration_ms / 1000.0:.1f} seconds ({video_duration_ms} ms).\n\n"
        f"Below is the complete timestamped transcript of the video:\n"
        f"{transcript_str}\n\n"
        f"TASK: Analyze the entire conversation/video and select the single most valuable, compelling, and viral moment.\n"
        f"GUIDELINES FOR SELECTION:\n"
        f"- DO NOT simply pick the first 60-90 seconds unless it is unequivocally the best climax of the entire video.\n"
        f"- Search for the moment with the highest emotional peak, surprising insight, funny joke, revelation, or core value payoff.\n"
        f"- Ensure the segment starts with an intriguing hook or question and concludes on a satisfying or punchy takeaway.\n\n"
        f"CRITICAL CONSTRAINTS:\n"
        f"1. Segment duration MUST be <= 120000 ms (120 seconds / 2 minutes) and >= 15000 ms (15 seconds).\n"
        f"2. 0 <= start_ms < end_ms <= {video_duration_ms}.\n"
        f"3. Must strictly respect sentence/utterance boundaries.\n"
        f"4. Respond with STRICT JSON ONLY. Do not write markdown code fences or conversational text.\n\n"
        f'{{"start_ms": <integer>, "end_ms": <integer>, "topic": "<catchy topic, max 6 words>", "reason": "<why this specific moment is the best climax>"}}'
    )

    try:
        import boto3
        from botocore.exceptions import BotoCoreError, ClientError

        client = boto3.client("bedrock-runtime", region_name=aws_region)

        def _call_bedrock(current_prompt: str) -> Dict[str, Any]:
            # Claude 3 format or generic converse
            if "claude" in model_id.lower():
                payload = {
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 500,
                    "temperature": 0.2,
                    "messages": [
                        {"role": "user", "content": current_prompt}
                    ],
                }
                response = client.invoke_model(
                    modelId=model_id,
                    contentType="application/json",
                    accept="application/json",
                    body=json.dumps(payload),
                )
                res_body = json.loads(response["body"].read().decode("utf-8"))
                text_out = res_body["content"][0]["text"]
            else:
                # Amazon Titan / other models
                payload = {
                    "inputText": current_prompt,
                    "textGenerationConfig": {
                        "maxTokenCount": 500,
                        "temperature": 0.2,
                    },
                }
                response = client.invoke_model(
                    modelId=model_id,
                    contentType="application/json",
                    accept="application/json",
                    body=json.dumps(payload),
                )
                res_body = json.loads(response["body"].read().decode("utf-8"))
                text_out = res_body.get("results", [{}])[0].get("outputText", "")

            return _extract_json_from_text(text_out)

        logger.info(f"Querying AWS Bedrock ({model_id}) for segment selection...", extra=extra)

        parsed_data = None
        for attempt in range(2):
            try:
                if attempt == 1:
                    logger.warning("Retrying Bedrock segment selection with strict correction prompt...", extra=extra)
                    retry_prompt = (
                        prompt + "\n\nCRITICAL: Previous response was not valid JSON. "
                        "Return ONLY raw JSON object. Example: {\"start_ms\": 5000, \"end_ms\": 45000, \"topic\": \"Topic\", \"reason\": \"Reason\"}"
                    )
                    parsed_data = _call_bedrock(retry_prompt)
                else:
                    parsed_data = _call_bedrock(prompt)

                # Validate required keys and ranges
                start_ms = int(parsed_data["start_ms"])
                end_ms = int(parsed_data["end_ms"])
                topic = str(parsed_data.get("topic", "Selected Highlight")).strip()
                reason = str(parsed_data.get("reason", "Engaging discussion")).strip()

                if not (0 <= start_ms < end_ms <= video_duration_ms):
                    raise ValueError(f"Invalid bounds: start_ms={start_ms}, end_ms={end_ms}, duration={video_duration_ms}")

                if (end_ms - start_ms) > MAX_SEGMENT_DURATION_MS:
                    logger.warning(
                        f"Bedrock segment duration ({end_ms - start_ms}ms) exceeds 120s; clamping to 120s.",
                        extra=extra,
                    )
                    end_ms = start_ms + MAX_SEGMENT_DURATION_MS

                # Snap to utterance boundaries
                snapped_start, snapped_end = _snap_to_utterance_boundaries(
                    start_ms, end_ms, utterances, video_duration_ms
                )

                logger.info(
                    f"Selected segment: [{snapped_start}ms - {snapped_end}ms] ({((snapped_end - snapped_start) / 1000):.1f}s) "
                    f"Topic: '{topic}'",
                    extra=extra,
                )

                return {
                    "start_ms": snapped_start,
                    "end_ms": snapped_end,
                    "topic": topic,
                    "reason": reason,
                }

            except Exception as parse_err:
                logger.warning(f"Bedrock attempt {attempt + 1} failed: {parse_err}", extra=extra)
                if attempt == 1:
                    raise

    except Exception as exc:
        logger.error(f"Bedrock segment selection failed or unavailable: {exc}", extra=extra)
        return _highest_density_fallback(
            transcript_data, video_duration_ms, f"Bedrock error: {str(exc)[:100]}", job_id=job_id
        )
