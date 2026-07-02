from agents.schemas import AgentResponse


def test_schema_validation_accepts_required_contract():
    response = AgentResponse(
        answer="Checked CRM data.",
        status="ok",
        detected_issues=[],
        recommended_actions=["Review draft."],
        tools_used=["load_crm_data"],
        confidence=0.8,
        needs_human_approval=False,
        reasoning_summary="Summary only.",
    )

    assert response.status == "ok"
    assert response.confidence == 0.8
