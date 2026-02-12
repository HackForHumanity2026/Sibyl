"""Claims Agent - extracts verifiable sustainability claims from reports.

Implements FRD 3.

Model: Gemini 3 Flash (1M token context window handles full 200-page PDFs)
"""

from app.agents.state import SibylState


async def extract_claims(state: SibylState) -> dict:
    """
    Extract verifiable sustainability claims from the parsed document.

    Categorizes each claim by type (geographic, quantitative, legal_governance,
    strategic, environmental) and tags with source page, preliminary IFRS mapping,
    and priority.

    Args:
        state: Current pipeline state with document content

    Returns:
        Partial state update with extracted claims
    """
    pass
