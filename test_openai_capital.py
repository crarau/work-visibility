import pytest
from openai import OpenAI
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize the OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def get_openai_response(prompt):
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=50
    )
    return response.choices[0].message.content.strip()

def test_capital_of_france():
    # Ask for the capital of France
    question = "What is the capital of France?"
    response = get_openai_response(question)
    
    print(f"\nQuestion: {question}")
    print(f"Response: {response}")
    
    # Check if the response contains "Paris"
    assert "Paris" in response, f"Expected 'Paris' in the response, but got: {response}"
    
    # Evaluate the response
    evaluation_prompt = f"""
    Evaluate the accuracy of the following response to the question "{question}":
    
    Response: {response}
    
    Is this response accurate? Answer with Yes or No, followed by a brief explanation.
    """
    
    evaluation = get_openai_response(evaluation_prompt)
    
    print(f"\nEvaluation: {evaluation}")
    
    # Check if the evaluation confirms accuracy
    assert "Yes" in evaluation, f"Expected the evaluation to confirm accuracy, but got: {evaluation}"

if __name__ == "__main__":
    pytest.main([__file__])
