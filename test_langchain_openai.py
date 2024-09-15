import pytest
from unittest.mock import patch
from langchain_openai import OpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

@pytest.fixture
def mock_openai_completion():
    with patch('langchain_openai.OpenAI.invoke') as mock_invoke:
        mock_invoke.return_value = "This is a mocked response from OpenAI."
        yield mock_invoke

def test_langchain_openai_integration(mock_openai_completion):
    # Initialize the OpenAI language model
    llm = OpenAI(temperature=0.7)

    # Create a prompt template
    template = "What is a brief summary of {topic}?"
    prompt = PromptTemplate.from_template(template)

    # Create a chain
    chain = (
        {"topic": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )

    # Run the chain
    result = chain.invoke("artificial intelligence")

    # Assert that the mock was called
    mock_openai_completion.assert_called_once()

    # Assert the result
    assert isinstance(result, str)
    assert result == "This is a mocked response from OpenAI."

    # You can add more specific assertions based on your expected output
    assert "mocked response" in result
