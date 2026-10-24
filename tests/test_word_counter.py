"""Check the shared tokenization convention and the essay-length boundaries."""

import pytest

from agent.tools.compute_tool import count_words


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("", 0),
        (" \t\r\n ", 0),
        ("... ! ? --", 0),
        ("I like public transport.", 4),
        ("First line.\nSecond\tline.", 4),
        ("Hello, world!", 2),
        ("don't can't student's", 3),
        ("state-of-the-art well-known", 2),
        ("2026 3.5 COVID-19", 4),
        ("hello 世界", 1),
        # The agreed regex only treats the straight apostrophe as a joiner.
        ("don’t", 2),
    ],
)
def test_count_words(text: str, expected: int) -> None:
    assert count_words(text) == expected


@pytest.mark.parametrize("word_count", [149, 150, 151, 249, 250, 251])
def test_count_words_at_task_length_boundaries(word_count: int) -> None:
    assert count_words("word " * word_count) == word_count


@pytest.mark.parametrize("invalid_text", [None, 123, True, ["word"], b"word"])
def test_reject_non_string_text(invalid_text: object) -> None:
    with pytest.raises(TypeError, match="text must be a string"):
        count_words(invalid_text)
