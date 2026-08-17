from typing import TypedDict, List, Dict, Optional, Annotated
from langgraph.graph import StateGraph, START, END
from agents import orchestrator_node, asset_node, design_node, backend_node, execution_node, run_commands_node

# Phase 2: Core LangGraph Setup - Define the AgentState
class AgentState(TypedDict):
    # User Inputs
    business_description: str
    tone: str
    brand_colors: Optional[List[str]]
    user_feedback: Optional[str]
    
    # Agent Outputs
    website_plan: Optional[Dict]
    assets: Optional[Dict]
    frontend_code: Optional[str]
    backend_code: Optional[str]
    
    # Control Flow
    review_status: str
    review_feedback: Optional[str]
    pending_commands: List[str]
    human_approval: bool
    current_stage: str

# Create the graph builder
graph_builder = StateGraph(AgentState)

graph_builder.add_node("orchestrator", orchestrator_node)
graph_builder.add_node("asset", asset_node)
graph_builder.add_node("design", design_node)
graph_builder.add_node("backend", backend_node)
graph_builder.add_node("execution", execution_node)
graph_builder.add_node("run_commands", run_commands_node)

def orchestrator_router(state: AgentState):
    stage = state.get("current_stage")
    if stage == "generating_assets":
        return "asset"
    elif stage == "execution":
        return "execution"
    elif stage == "coding_frontend": # Triggered when the review fails
        return "design"
    # Default fallback
    return "asset"

graph_builder.add_edge(START, "orchestrator")
graph_builder.add_conditional_edges("orchestrator", orchestrator_router)
graph_builder.add_edge("asset", "design")
graph_builder.add_edge("design", "backend")
graph_builder.add_edge("backend", "orchestrator") # Loops back for review
graph_builder.add_edge("execution", "run_commands")
graph_builder.add_edge("run_commands", END)

# In order to pause the graph, we must use a checkpointer to save state
from langgraph.checkpoint.memory import MemorySaver
memory = MemorySaver()

# Compile the graph with a breakpoint before the commands are executed
app = graph_builder.compile(
    checkpointer=memory,
    interrupt_before=["run_commands"]
)
