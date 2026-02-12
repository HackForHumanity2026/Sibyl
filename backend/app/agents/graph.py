"""LangGraph StateGraph definition stub for the Sibyl pipeline.

This file defines the graph structure but does NOT compile or execute it.
Node implementations are added in subsequent FRDs.

Node -> FRD Mapping:
- parse_document     -> FRD 2 (PDF Upload & Ingestion)
- extract_claims     -> FRD 3 (Claims Agent)
- orchestrate        -> FRD 5 (Orchestrator Agent)
- investigate_geography -> FRD 10 (Geography Agent)
- investigate_legal  -> FRD 6 (Legal Agent)
- investigate_news   -> FRD 8 (News/Media Agent)
- investigate_academic -> FRD 9 (Academic/Research Agent)
- investigate_data   -> FRD 7 (Data/Metrics Agent)
- judge_evidence     -> FRD 11 (Judge Agent)
- compile_report     -> FRD 13 (Source of Truth Report)
"""

from langgraph.graph import StateGraph

from app.agents.state import SibylState

# Node name constants
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

# Graph definition (not compiled)
# The StateGraph is created here but nodes and edges are added in subsequent FRDs
graph_builder = StateGraph(SibylState)

# TODO: Add nodes in subsequent FRDs
# graph_builder.add_node(PARSE_DOCUMENT, parse_document_node)
# graph_builder.add_node(EXTRACT_CLAIMS, extract_claims_node)
# ...

# TODO: Add edges in subsequent FRDs
# graph_builder.add_edge(PARSE_DOCUMENT, EXTRACT_CLAIMS)
# graph_builder.add_edge(EXTRACT_CLAIMS, ORCHESTRATE)
# ...

# TODO: Compile graph in FRD 5
# graph = graph_builder.compile()
