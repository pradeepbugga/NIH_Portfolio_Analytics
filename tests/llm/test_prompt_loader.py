from unittest.mock import patch
import pytest
from core.llm.prompt_loader import load_prompt


def test_load_prompt(tmp_path):
    """
    Test that load_prompt correctly loads a prompt from the prompts directory."""

    prompt_dir = tmp_path / "prompts"
    prompt_dir.mkdir()

    prompt_file = prompt_dir / "summary.txt"
    prompt_file.write_text("Summarize this grant.")

    with patch("core.llm.prompt_loader.PROMPT_DIR", prompt_dir):

        prompt = load_prompt("summary")

    assert prompt == "Summarize this grant."


def test_load_prompt_missing_file(tmp_path):
    """
    Test that load_prompt raises a FileNotFoundError when the specified prompt file does not exist.
    """

    prompt_dir = tmp_path / "prompts"
    prompt_dir.mkdir()

    with patch("core.llm.prompt_loader.PROMPT_DIR", prompt_dir):

        with pytest.raises(FileNotFoundError):
            load_prompt("summary")
