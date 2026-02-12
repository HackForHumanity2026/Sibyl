"""Judge Agent - evaluates evidence and issues verdicts with cyclic validation.

Implements FRD 11.

Model: Claude Opus 4.5 (highest-quality reasoning for judgment calls)
"""

from app.agents.state import SibylState


async def judge_evidence(state: SibylState) -> dict:
    """
    Evaluate evidence from specialist agents and issue verdicts.

    Evaluation criteria:
    - Sufficiency: Enough evidence to reach a verdict?
    - Consistency: Do findings from different agents align?
    - Quality: Are sources credible? Direct or circumstantial?
    - Completeness: All relevant angles investigated?

    Verdicts:
    - verified: Multiple independent sources corroborate
    - unverified: No external evidence found
    - contradicted: Evidence directly contradicts claim
    - insufficient_evidence: Some evidence but not enough

    May request re-investigation if evidence is insufficient (cyclic validation).

    Args:
        state: Current pipeline state with all agent findings

    Returns:
        Partial state update with verdicts and/or reinvestigation requests
    """
    pass
