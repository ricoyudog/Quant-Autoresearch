from pathlib import Path


def test_program_includes_research_and_memory_guidance_sections():
    content = Path("program.md").read_text()

    assert "## Research Capabilities" in content
    assert "## Memory Access Patterns" in content
