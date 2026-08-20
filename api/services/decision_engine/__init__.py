"""TruthLens Decision Engine — package initializer."""

from .analyzer import run_decision_engine
from .schemas import AssessmentResult, EvidenceSignals
from .rules import (
    CAT_LIKELY_AUTHENTIC,
    CAT_POTENTIAL_DEEPFAKE,
    CAT_BOTH_SYNTHETIC,
    CAT_AI_DIFF_PERSON,
    CAT_SYNTH_REF_AUTH_SUS,
    CAT_AUTH_DIFF_PERSON,
    CAT_INCONCLUSIVE,
    CAT_UNABLE_TO_VERIFY,
    RISK_HIGH,
    RISK_MEDIUM,
    RISK_LOW,
    RISK_UNKNOWN,
    CONF_HIGH,
    CONF_MEDIUM,
    CONF_LOW,
)

__all__ = [
    "run_decision_engine",
    "AssessmentResult",
    "EvidenceSignals",
    "CAT_LIKELY_AUTHENTIC",
    "CAT_POTENTIAL_DEEPFAKE",
    "CAT_BOTH_SYNTHETIC",
    "CAT_AI_DIFF_PERSON",
    "CAT_SYNTH_REF_AUTH_SUS",
    "CAT_AUTH_DIFF_PERSON",
    "CAT_INCONCLUSIVE",
    "CAT_UNABLE_TO_VERIFY",
    "RISK_HIGH",
    "RISK_MEDIUM",
    "RISK_LOW",
    "RISK_UNKNOWN",
    "CONF_HIGH",
    "CONF_MEDIUM",
    "CONF_LOW",
]
