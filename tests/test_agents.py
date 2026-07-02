from agents.context import prepare_shared_context
from agents.multi_agent import run_agent as run_multi
from agents.schemas import AgentResponse
from agents.single_agent import run_agent as run_single
from tools.tool_registry import build_tool_registry


def test_both_agents_return_agent_response():
    prompt = "Find duplicate accounts in the CRM data."
    context = prepare_shared_context(prompt)
    registry = build_tool_registry()

    single = run_single(prompt, context, registry)
    multi = run_multi(prompt, context, registry)

    assert isinstance(single, AgentResponse)
    assert isinstance(multi, AgentResponse)
    assert single.status == "ok"
    assert multi.status == "ok"
    assert "check_duplicate_records" in single.tools_used
    assert "check_duplicate_records" in multi.tools_used
