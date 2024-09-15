import json
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from typing import Literal

# Define a Pydantic model for your schema
class ItemSchema(BaseModel):
    name: str = Field(description="The name of the item")
    status: Literal["available", "out_of_stock"] = Field(description="The item's availability status")

# Function to call OpenAI and enforce JSON schema
def call_openai_with_strict_json(input_text: str) -> dict:
    # Create an instance of the schema for validation
    output_parser = PydanticOutputParser(pydantic_object=ItemSchema)

    # Initialize ChatOpenAI API client
    llm = ChatOpenAI(model="gpt-4-turbo-preview", temperature=0)

    # Define your prompt template
    prompt = ChatPromptTemplate.from_messages([
        ("system", "Extract structured data according to the following schema: {format_instructions}"),
        ("human", "{input_text}")
    ])

    # Create the chain
    chain = prompt | llm | output_parser

    # Call the model with your input text
    response = chain.invoke({
        "format_instructions": output_parser.get_format_instructions(),
        "input_text": input_text
    })

    # The response is already a Pydantic object, so we can convert it to a dict
    return response.dict()