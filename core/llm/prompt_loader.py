from pathlib import Path

PROMPT_DIR = Path(__file__).parent / "prompts"


def load_prompt(name: str) -> str:
    """
    Load a prompt from the prompts directory.

    Examples
    --------
    load_prompt("classification/research_tool")
    load_prompt("summary")
    """

    path = PROMPT_DIR / f"{name}.txt"

    return path.read_text()
