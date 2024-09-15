import pytest
from openai_module import call_openai_with_strict_json  # Import the function from your module


# Define the test function
def test_openai_json_output():
    # Define test input and expected structured output
    input_text = "The product Apple Watch is available."
    expected_output = {
        "name": "Apple Watch",
        "status": "available"
    }

    # Invoke the OpenAI function
    response = call_openai_with_strict_json(input_text)

    # Assert that the response matches the expected output
    assert response == expected_output

def test_invalid_status():
    input_text = "The product MacBook is something else."
    
    # Invoke the OpenAI function
    response = call_openai_with_strict_json(input_text)

    # Assert that the status is either "available" or "out_of_stock"
    assert response["status"] in ["available", "out_of_stock"]
    assert response["name"] == "MacBook"