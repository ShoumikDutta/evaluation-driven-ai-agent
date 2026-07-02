from run_comparison import run_comparison


def test_run_comparison_works_with_sample_prompt():
    result = run_comparison("Find duplicate accounts in the CRM data.", mode="both", save_traces=False)

    assert result["single"]["response"]["status"] == "ok"
    assert result["multi"]["response"]["status"] == "ok"
    assert result["comparison"]["status_match"] is True
