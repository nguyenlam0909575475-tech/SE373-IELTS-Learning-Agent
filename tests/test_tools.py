"""Unit tests for repository Task rounding policy and input verification."""

from math import nextafter

import pytest

from agent.tools.compute_tool import compute_band, compute_task_band


@pytest.mark.parametrize(
    ("scores", "expected"),
    [
        ([0, 0, 0, 0], 0.0),
        ([9, 9, 9, 9], 9.0),
        ([6, 6, 6, 6], 6.0),
        ([6, 6, 7, 7], 6.5),
        ([6, 6, 6, 7], 6.5),
        ([6, 7, 7, 7], 7.0),
        ([6, 6.5, 7, 7.5], 7.0),
        ([0, 0, 0, 0.5], 0.0),
        ([0, 0, 0.5, 1], 0.5),
    ],
)
def test_compute_band(scores: list[int | float], expected: float) -> None:
    assert compute_band(scores) == expected


@pytest.mark.parametrize("lower_band", range(9))
def test_quarter_rounds_up(lower_band: int) -> None:
    scores = [lower_band, lower_band, lower_band, lower_band + 1]
    assert compute_band(scores) == lower_band + 0.5


@pytest.mark.parametrize("lower_band", range(9))
def test_three_quarter_rounds_up(lower_band: int) -> None:
    scores = [lower_band, lower_band + 1, lower_band + 1, lower_band + 1]
    assert compute_band(scores) == lower_band + 1


@pytest.mark.parametrize(
    ("score", "expected"),
    [
        (nextafter(6.25, 0.0), 6.0),
        (nextafter(6.25, 9.0), 6.5),
        (nextafter(6.75, 0.0), 6.5),
        (nextafter(6.75, 9.0), 7.0),
    ],
)
def test_values_immediately_around_rounding_boundaries(
    score: float, expected: float
) -> None:
    assert compute_band([score] * 4) == expected


def test_accept_tuple_of_scores() -> None:
    assert compute_band((6, 6, 6, 7)) == 6.5


def test_previous_tool_name_remains_compatible() -> None:
    assert compute_task_band([6, 6, 6, 7]) == 6.5


@pytest.mark.parametrize("scores", [[], [6], [6, 6, 6], [6, 6, 6, 6, 6]])
def test_reject_wrong_number_of_scores(scores: list[int]) -> None:
    with pytest.raises(ValueError, match="exactly four"):
        compute_band(scores)


@pytest.mark.parametrize("scores", [None, 6, "6667", {"band": 6}])
def test_reject_non_sequence_input(scores: object) -> None:
    with pytest.raises(TypeError, match="sequence of four numbers"):
        compute_band(scores)


@pytest.mark.parametrize("invalid_score", [True, None, "6", 6 + 0j])
def test_reject_non_numeric_scores(invalid_score: object) -> None:
    with pytest.raises(TypeError, match=r"scores\[0\].*int or float"):
        compute_band([invalid_score, 6, 6, 6])


@pytest.mark.parametrize("invalid_score", [float("nan"), float("inf"), -float("inf")])
def test_reject_non_finite_scores(invalid_score: float) -> None:
    with pytest.raises(ValueError, match="finite"):
        compute_band([invalid_score, 6, 6, 6])


@pytest.mark.parametrize("invalid_score", [-0.5, 9.5, 10**100])
def test_reject_out_of_range_scores(invalid_score: int | float) -> None:
    with pytest.raises(ValueError, match="between 0 and 9"):
        compute_band([invalid_score, 6, 6, 6])
