import pytest
from openai import OpenAI
import os
from dotenv import load_dotenv
import json

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

def ttttest_capital_of_france():
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

def test_openai_query_function():
    # Prepare the messages and tools
    messages = [
        {
            "role": "system",
            "content": "You are a helpful assistant. The current date is August 6, 2024. You help users query for the data they are looking for by calling the query function."
        },
        {
            "role": "user",
            "content": "look up all my orders in may of last year that were fulfilled but not delivered on time"
        }
    ]

    tools = [
        {
            "type": "function",
            "function": {
                "name": "query",
                "description": "Execute a query.",
                "strict": True,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "table_name": {"type": "string", "enum": ["orders"]},
                        "columns": {
                            "type": "array",
                            "items": {
                                "type": "string",
                                "enum": ["id", "status", "expected_delivery_date", "delivered_at", "shipped_at", "ordered_at", "canceled_at"]
                            }
                        },
                        "conditions": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "column": {"type": "string"},
                                    "operator": {"type": "string", "enum": ["=", ">", "<", ">=", "<=", "!="]},
                                    "value": {
                                        "anyOf": [
                                            {"type": "string"},
                                            {"type": "number"},
                                            {
                                                "type": "object",
                                                "properties": {"column_name": {"type": "string"}},
                                                "required": ["column_name"],
                                                "additionalProperties": False
                                            }
                                        ]
                                    }
                                },
                                "required": ["column", "operator", "value"],
                                "additionalProperties": False
                            }
                        },
                        "order_by": {"type": "string", "enum": ["asc", "desc"]}
                    },
                    "required": ["table_name", "columns", "conditions", "order_by"],
                    "additionalProperties": False
                }
            }
        }
    ]

    # Send the request to OpenAI API
    response = client.chat.completions.create(
        model="gpt-4o-2024-08-06",  # Note: Using gpt-4-0613 as gpt-4o-2024-08-06 is not available yet
        messages=messages,
        tools=tools
    )

    # Print the full response for inspection
    print("Full API Response:")
    print(json.dumps(response.model_dump(), indent=2))

    # Extract and print the formatted "arguments" part
    if response.choices and response.choices[0].message.tool_calls:
        arguments_json = response.choices[0].message.tool_calls[0].function.arguments
        print("\nFormatted 'arguments' content:")
        print(json.dumps(json.loads(arguments_json), indent=2))

    # Parse and check the function arguments
    function_args = json.loads(response.choices[0].message.tool_calls[0].function.arguments)
    
    # Check table name
    assert function_args["table_name"] == "orders", "Expected 'orders' as the table name"
    
    # Check columns
    required_columns = {"id", "status", "expected_delivery_date", "delivered_at"}
    assert required_columns.issubset(function_args["columns"]), f"Expected columns to include {required_columns}"
    
    # Check conditions
    conditions = function_args["conditions"]
    assert len(conditions) == 4, "Expected 4 conditions"
    
    expected_conditions = [
        {"column": "status", "operator": "=", "value": "fulfilled"},
        {"column": "ordered_at", "operator": ">=", "value": "2023-05-01"},
        {"column": "ordered_at", "operator": "<=", "value": "2023-05-31"},
        {
            "column": "delivered_at",
            "operator": ">",
            "value": {"column_name": "expected_delivery_date"}
        }
    ]
    
    for expected_condition in expected_conditions:
        assert any(
            all(item in condition.items() for item in expected_condition.items())
            for condition in conditions
        ), f"Expected condition not found: {expected_condition}"
    
    # Check order_by
    assert function_args["order_by"] == "asc", "Expected ascending order"

if __name__ == "__main__":
    pytest.main([__file__])
