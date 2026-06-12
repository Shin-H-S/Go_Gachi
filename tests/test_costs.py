from backend.app.services.costs import calculate_image_cost, calculate_text_cost


def test_calculate_image_cost_uses_gpt_image_2_token_rates() -> None:
    cost = calculate_image_cost({"input_tokens": 1000, "output_tokens": 2000})

    assert cost == 0.068


def test_calculate_text_cost_uses_model_rates() -> None:
    expensive = calculate_text_cost({"input_tokens": 1000, "output_tokens": 2000}, model="gpt-5.5")
    default = calculate_text_cost({"input_tokens": 1000, "output_tokens": 2000})

    assert expensive == 0.065
    assert default == 0.00975
