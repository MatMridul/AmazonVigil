"""Bedrock Multimodal Threat Evaluator (Task 1.4).

Wraps ``boto3.client('bedrock-runtime')`` targeting
``anthropic.claude-3-5-sonnet-20241022``. Constructs a structured multimodal
prompt from the resized WebP frame, audio context, wearer bio-context, and the 4D
integrity vector, then parses the response into a strict ``ThreatAssessment``.

Includes a deterministic heuristic fallback for degraded / mock mode so the whole
Phase 1 pipeline runs offline with zero AWS credentials (DR-04).
"""

from __future__ import annotations

import base64
import json
import os
import re
from typing import Any

from src.core.state_machine import classify_score, recommended_action
from src.core.types import (
    AudioSentiment,
    DetectedSubject,
    IntegrityVector,
    MeshAction,
    ThreatAssessment,
    ThreatLevel,
    WearerBioContext,
)

DEFAULT_MODEL_ID = "anthropic.claude-3-5-sonnet-20241022"
BEDROCK_TIMEOUT_MS = 1500  # System 2 budget (SPEC.md §7 dual-brain)

_JSON_FENCE = re.compile(r"```(?:json)?\s*(\{.*?\})\s*```", re.DOTALL)


class BedrockThreatEvaluator:
    """Multimodal threat evaluator with live-Bedrock and offline-mock modes."""

    def __init__(
        self,
        *,
        model_id: str = DEFAULT_MODEL_ID,
        region: str | None = None,
        mock: bool | None = None,
    ) -> None:
        self.model_id = model_id
        self.region = region or os.getenv("AWS_REGION", "us-east-1")
        # mock defaults to True unless VIGIL_MODE=live explicitly set.
        if mock is None:
            mock = os.getenv("VIGIL_MODE", "simulation").lower() != "live"
        self.mock = mock
        self._client: Any = None  # lazily created only in live mode (boto3 client)

    # ----------------------------------------------------------------- #
    # Public API
    # ----------------------------------------------------------------- #
    def evaluate(
        self,
        *,
        frame_webp: bytes | None,
        audio_transcript: str,
        acoustic_db: float,
        bio: WearerBioContext,
        integrity: IntegrityVector,
    ) -> ThreatAssessment:
        """Return a validated ThreatAssessment for one perimeter event."""
        if self.mock:
            return self._heuristic_fallback(
                audio_transcript=audio_transcript,
                acoustic_db=acoustic_db,
                bio=bio,
                integrity=integrity,
            )
        try:
            raw = self._invoke_bedrock(
                frame_webp=frame_webp,
                audio_transcript=audio_transcript,
                acoustic_db=acoustic_db,
                bio=bio,
                integrity=integrity,
            )
            return self._parse_assessment(raw)
        except Exception:
            # Degraded-mode: never crash the safety pipeline on a cloud fault.
            return self._heuristic_fallback(
                audio_transcript=audio_transcript,
                acoustic_db=acoustic_db,
                bio=bio,
                integrity=integrity,
            )

    # ----------------------------------------------------------------- #
    # Prompt construction
    # ----------------------------------------------------------------- #
    def build_prompt(
        self,
        *,
        frame_webp: bytes | None,
        audio_transcript: str,
        acoustic_db: float,
        bio: WearerBioContext,
        integrity: IntegrityVector,
    ) -> dict:
        """Construct the Anthropic messages payload (multimodal)."""
        content: list[dict] = []
        if frame_webp:
            content.append(
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/webp",
                        "data": base64.b64encode(frame_webp).decode("ascii"),
                    },
                }
            )
        context = {
            "audio_transcript": audio_transcript,
            "acoustic_db": acoustic_db,
            "host_state": bio.host_state.value,
            "is_asleep": bio.is_asleep,
            "integrity_vector": {
                "phi_m": integrity.phi_m,
                "phi_v": integrity.phi_v,
                "phi_a": integrity.phi_a,
                "phi_net": integrity.phi_net,
            },
        }
        content.append(
            {
                "type": "text",
                "text": (
                    "You are the Amazon Vigil threat evaluator. Assess this "
                    "perimeter event and respond with ONLY a JSON object matching "
                    "the ThreatAssessment schema (threat_level, threat_score, "
                    "detected_subject, visual_findings, audio_sentiment, "
                    "recommended_mesh_action, justification).\n\n"
                    f"Context: {json.dumps(context)}"
                ),
            }
        )
        return {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 1024,
            "messages": [{"role": "user", "content": content}],
        }

    # ----------------------------------------------------------------- #
    # Live Bedrock invocation
    # ----------------------------------------------------------------- #
    def _invoke_bedrock(self, **kwargs) -> str:
        import boto3  # imported lazily so mock mode needs no AWS SDK at import time

        if self._client is None:
            self._client = boto3.client("bedrock-runtime", region_name=self.region)
        body = json.dumps(self.build_prompt(**kwargs))
        resp = self._client.invoke_model(modelId=self.model_id, body=body)
        payload = json.loads(resp["body"].read())
        # Anthropic-on-Bedrock returns content blocks; concatenate text blocks.
        blocks = payload.get("content", [])
        return "".join(b.get("text", "") for b in blocks if b.get("type") == "text")

    # ----------------------------------------------------------------- #
    # Parsing & validation
    # ----------------------------------------------------------------- #
    def _parse_assessment(self, raw: str) -> ThreatAssessment:
        """Parse model text into ThreatAssessment, repairing ```json fences."""
        text = raw.strip()
        fenced = _JSON_FENCE.search(text)
        if fenced:
            text = fenced.group(1)
        else:
            start, end = text.find("{"), text.rfind("}")
            if start != -1 and end != -1 and end > start:
                text = text[start : end + 1]
        data = json.loads(text)
        return ThreatAssessment.model_validate(data)

    # ----------------------------------------------------------------- #
    # Deterministic offline heuristic (mock / degraded mode)
    # ----------------------------------------------------------------- #
    def _heuristic_fallback(
        self,
        *,
        audio_transcript: str,
        acoustic_db: float,
        bio: WearerBioContext,
        integrity: IntegrityVector,
    ) -> ThreatAssessment:
        """Transparent rule-based assessment when Bedrock is unavailable."""
        transcript = (audio_transcript or "").lower()
        findings: list[str] = []
        score = 0.05

        if integrity.optical_tampered:
            score = max(score, 0.70)
            findings.append("optical_tamper_phi_v_zero")

        breach_words = ("scrap", "pry", "glass", "break", "jiggl", "crowbar")
        hostile_words = ("threat", "kill", "hostile", "weapon", "gun", "knife")
        if any(w in transcript for w in hostile_words):
            score = max(score, 0.90)
            findings.append("hostile_speech_detected")
            sentiment = AudioSentiment.HOSTILE
        elif any(w in transcript for w in breach_words):
            score = max(score, 0.70)
            findings.append("breach_acoustics_detected")
            sentiment = AudioSentiment.BREACH_NOISE
        elif transcript:
            sentiment = AudioSentiment.NEUTRAL
        else:
            sentiment = AudioSentiment.INDETERMINATE

        if acoustic_db >= 85.0:
            score = max(score, 0.55)
            findings.append("high_decibel_event")

        level = classify_score(score)
        action = recommended_action(level)

        if level == ThreatLevel.L0_SAFE:
            subject = DetectedSubject.BENIGN_STRANGER
        elif level == ThreatLevel.L1_AMBIGUOUS:
            subject = DetectedSubject.SUSPICIOUS_STRANGER
        else:
            subject = DetectedSubject.HOSTILE_INTRUDER

        if action == MeshAction.DISPATCH_EMERGENCY and bio.host_state.value == "H_distress":
            findings.append("silent_duress_protocol")

        return ThreatAssessment(
            threat_level=level,
            threat_score=round(score, 4),
            detected_subject=subject,
            visual_findings=findings,
            audio_sentiment=sentiment,
            recommended_mesh_action=action,
            justification=(
                "Offline heuristic fallback (Bedrock degraded/mock mode): "
                f"score={round(score, 4)} from integrity+acoustic+transcript signals."
            ),
        )
