from run_eval_harness import load_eval_cases


def test_eval_cases_load_successfully():
    cases = load_eval_cases()

    assert len(cases) >= 20
    assert {case["category"] for case in cases} >= {"normal", "edge", "long_input", "prompt_injection", "human_loop"}
