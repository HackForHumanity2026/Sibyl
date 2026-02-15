"""LangGraph StateGraph definition for the Sibyl pipeline.

Implements FRD 5 Section 1.

Defines the compiled, executable LangGraph StateGraph that implements the
full multi-agent pipeline from claims extraction through verdict generation.
"""

import logging
from typing import Literal

from langgraph.graph import END, START, StateGraph

from app.agents.state import SibylState
from app.core.config import settings

logger = logging.getLogger(__name__)

# =============================================================================
# Node name constants
# =============================================================================

PARSE_DOCUMENT = "parse_document"
EXTRACT_CLAIMS = "extract_claims"
ORCHESTRATE = "orchestrate"
INVESTIGATE_GEOGRAPHY = "investigate_geography"
INVESTIGATE_LEGAL = "investigate_legal"
INVESTIGATE_NEWS = "investigate_news"
INVESTIGATE_ACADEMIC = "investigate_academic"
INVESTIGATE_DATA = "investigate_data"
JUDGE_EVIDENCE = "judge_evidence"
COMPILE_REPORT = "compile_report"

# =============================================================================
# Agent-to-Node mappings
# =============================================================================

AGENT_TO_NODE: dict[str, str] = {
    "geography": INVESTIGATE_GEOGRAPHY,
    "legal": INVESTIGATE_LEGAL,
    "news_media": INVESTIGATE_NEWS,
    "academic": INVESTIGATE_ACADEMIC,
    "data_metrics": INVESTIGATE_DATA,
}

NODE_TO_AGENT: dict[str, str] = {v: k for k, v in AGENT_TO_NODE.items()}

# All specialist node names
SPECIALIST_NODES = list(AGENT_TO_NODE.values())

# =============================================================================
# Routing functions
# =============================================================================


def route_to_specialists(state: SibylState) -> list[str]:
    """Determine which specialist agents to invoke based on the routing plan.
    
    Returns a list of node names for agents with assigned claims.
    If no agents have assignments (e.g., re-investigation with only
    InfoRequests), routes directly to judge_evidence.
    
    Args:
        state: Current pipeline state with routing plan
        
    Returns:
        List of node names to route to
    """
    active_agents = set()
    
    for assignment in state.routing_plan:
        for agent in assignment.assigned_agents:
            if agent in AGENT_TO_NODE:
                node_name = AGENT_TO_NODE[agent]
                active_agents.add(node_name)
            else:
                logger.warning("Unknown agent in routing plan: %s", agent)
    
    if not active_agents:
        logger.info("No active agents in routing plan, routing to judge")
        return [JUDGE_EVIDENCE]
    
    logger.info("Routing to specialists: %s", list(active_agents))
    return list(active_agents)


def should_continue_or_compile(
    state: SibylState,
) -> Literal["orchestrate", "compile_report"]:
    """Determine whether to cycle back for re-investigation or compile.
    
    Returns "orchestrate" if:
      - There are pending reinvestigation_requests AND
      - iteration_count < max_iterations
    
    Returns "compile_report" otherwise.
    
    Args:
        state: Current pipeline state
        
    Returns:
        Next node name to route to
    """
    has_reinvestigation = len(state.reinvestigation_requests) > 0
    within_limit = state.iteration_count < state.max_iterations
    
    if has_reinvestigation and within_limit:
        logger.info(
            "Re-investigation requested (iteration %d/%d)",
            state.iteration_count,
            state.max_iterations,
        )
        return "orchestrate"
    
    logger.info("Proceeding to compile report")
    return "compile_report"


# =============================================================================
# Graph construction
# =============================================================================


def build_graph() -> StateGraph:
    """Build the Sibyl multi-agent pipeline graph.
    
    Creates a StateGraph with all nodes and edges for the full pipeline:
    - extract_claims: Extract claims from document (Claims Agent)
    - orchestrate: Route claims to specialists (Orchestrator)
    - investigate_*: Specialist agents (stubs in FRD 5)
    - judge_evidence: Evaluate evidence and issue verdicts
    - compile_report: Persist results and finalize
    
    Returns:
        Configured but not compiled StateGraph
    """
    # Import node functions here to avoid circular imports
    from app.agents.claims_agent import extract_claims
    from app.agents.orchestrator_agent import orchestrate
    from app.agents.geography_agent import investigate_geography
    from app.agents.legal_agent import investigate_legal
    from app.agents.news_media_agent import investigate_news
    from app.agents.academic_agent import investigate_academic
    from app.agents.data_metrics_agent import investigate_data
    from app.agents.judge_agent import judge_evidence
    from app.agents.compile_report import compile_report
    
    graph = StateGraph(SibylState)
    
    # Add nodes
    graph.add_node(EXTRACT_CLAIMS, extract_claims)
    graph.add_node(ORCHESTRATE, orchestrate)
    graph.add_node(INVESTIGATE_GEOGRAPHY, investigate_geography)
    graph.add_node(INVESTIGATE_LEGAL, investigate_legal)
    graph.add_node(INVESTIGATE_NEWS, investigate_news)
    graph.add_node(INVESTIGATE_ACADEMIC, investigate_academic)
    graph.add_node(INVESTIGATE_DATA, investigate_data)
    graph.add_node(JUDGE_EVIDENCE, judge_evidence)
    graph.add_node(COMPILE_REPORT, compile_report)
    
    # Entry edge
    graph.add_edge(START, EXTRACT_CLAIMS)
    graph.add_edge(EXTRACT_CLAIMS, ORCHESTRATE)
    
    # Orchestrator fans out to specialists via conditional edges
    graph.add_conditional_edges(
        ORCHESTRATE,
        route_to_specialists,
        {
            INVESTIGATE_GEOGRAPHY: INVESTIGATE_GEOGRAPHY,
            INVESTIGATE_LEGAL: INVESTIGATE_LEGAL,
            INVESTIGATE_NEWS: INVESTIGATE_NEWS,
            INVESTIGATE_ACADEMIC: INVESTIGATE_ACADEMIC,
            INVESTIGATE_DATA: INVESTIGATE_DATA,
            JUDGE_EVIDENCE: JUDGE_EVIDENCE,  # Skip specialists if no assignments
        },
    )
    
    # All specialist nodes converge to judge_evidence
    graph.add_edge(INVESTIGATE_GEOGRAPHY, JUDGE_EVIDENCE)
    graph.add_edge(INVESTIGATE_LEGAL, JUDGE_EVIDENCE)
    graph.add_edge(INVESTIGATE_NEWS, JUDGE_EVIDENCE)
    graph.add_edge(INVESTIGATE_ACADEMIC, JUDGE_EVIDENCE)
    graph.add_edge(INVESTIGATE_DATA, JUDGE_EVIDENCE)
    
    # Judge conditionally cycles back or proceeds to compile
    graph.add_conditional_edges(
        JUDGE_EVIDENCE,
        should_continue_or_compile,
        {
            "orchestrate": ORCHESTRATE,
            "compile_report": COMPILE_REPORT,
        },
    )
    
    # Terminal edge
    graph.add_edge(COMPILE_REPORT, END)
    
    return graph


def get_compiled_graph(checkpointer=None):
    """Compile the graph with optional PostgreSQL checkpointing.
    
    Args:
        checkpointer: Optional AsyncPostgresSaver for state persistence
        
    Returns:
        Compiled LangGraph ready for execution
    """
    graph = build_graph()
    return graph.compile(checkpointer=checkpointer)


async def get_checkpointer():
    """Create a PostgreSQL-backed checkpointer for LangGraph.
    
    Returns:
        AsyncPostgresSaver configured with the database URL
    """
    try:
        from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
        
        checkpointer = AsyncPostgresSaver.from_conn_string(
            settings.DATABASE_URL
        )
        await checkpointer.setup()  # Creates checkpoint tables if not exist
        return checkpointer
    except ImportError:
        logger.warning(
            "langgraph-checkpoint-postgres not installed, "
            "checkpointing disabled"
        )
        return None
    except Exception as e:
        logger.warning("Failed to setup checkpointer: %s", e)
        return None
