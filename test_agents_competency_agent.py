import pytest
from competency_agent import CompetencyAgent

@pytest.fixture
def competency_description():
    return "Understands the testing pyramid, and writes unit tests as well as higher level tests in accordance with it. Always writes tests to handle expected edge cases and errors gracefully, as well as happy paths."

def test_competency_agent_happy_path(competency_description):
    agent = CompetencyAgent(competency_description)
    pr_patch = """
    def add(a, b):
        return a + b

    def test_add():
        assert add(2, 3) == 5
    """
    pr_description = "Added addition functionality with unit tests."
    pr_link = "https://github.com/example/repo/pull/1"

    result = agent.analyze_pr(pr_patch, pr_description, pr_link)
    assert result["pr_link"] == pr_link
    assert "unit tests" in result["summary"].lower()
    assert "-" not in result["summary"]

def test_competency_agent_unhappy_path(competency_description):
    agent = CompetencyAgent(competency_description)
    pr_patch = """
    def multiply(a, b):
        return a * b
    """
    pr_description = "Added multiplication functionality without tests."
    pr_link = "https://github.com/example/repo/pull/2"

    result = agent.analyze_pr(pr_patch, pr_description, pr_link)
    assert result["pr_link"] == pr_link
    assert result["summary"] == "-"

def test_competency_agent_edge_case(competency_description):
    agent = CompetencyAgent(competency_description)
    pr_patch = """
    # No code changes
    """
    pr_description = "Updated README"
    pr_link = "https://github.com/example/repo/pull/3"

    result = agent.analyze_pr(pr_patch, pr_description, pr_link)
    assert result["pr_link"] == pr_link
    assert result["summary"] == "-"
