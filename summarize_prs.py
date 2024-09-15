import os
import hashlib
import json
from dotenv import load_dotenv
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from pymongo import MongoClient
from bson import ObjectId
from typing import List, Dict, Any
import logging

load_dotenv()

# MongoDB connection
MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client.github_prs
pr_collection = db.pull_requests
summary_collection = db.summaries

# OpenAI API key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Define the Pydantic model for the output
class PRSummary(BaseModel):
    summary: str = Field(description="A concise summary of the pull request")
    key_points: List[str] = Field(description="A list of key points from the pull request")
    sentiment: str = Field(description="The sentiment of the pull request: positive, neutral, or negative")

# Create the output parser
output_parser = PydanticOutputParser(pydantic_object=PRSummary)

# Create the ChatOpenAI model
model = ChatOpenAI(temperature=0.7, model="gpt-4")

# Prompt template
prompt_template = ChatPromptTemplate.from_template("""
Please summarize the following pull request:

Title: {title}
Body: {body}
Comments: {comments}

{format_instructions}
""")

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def generate_pr_summary(pr: Dict[str, Any]) -> Dict[str, Any]:
    # Convert ObjectId to string
    pr = {k: str(v) if isinstance(v, ObjectId) else v for k, v in pr.items()}

    pr_hash = hashlib.sha256(json.dumps(pr, sort_keys=True).encode()).hexdigest()
    existing_summary = summary_collection.find_one({"pr_hash": pr_hash})

    if existing_summary:
        logger.info(f"Found existing summary for PR #{pr['number']}")
        # Convert ObjectId to string in existing_summary
        existing_summary = {k: str(v) if isinstance(v, ObjectId) else v for k, v in existing_summary.items()}
        return existing_summary

    comments = [comment["body"] for comment in pr["comments"]]
    
    # Create the prompt
    prompt = prompt_template.format_prompt(
        title=pr["title"],
        body=pr["body"],
        comments=comments,
        format_instructions=output_parser.get_format_instructions()
    )
    
    try:
        # Generate the summary using the LangChain model
        output = model(prompt.to_messages())
        summary_dict = output_parser.parse(output.content)
        
        summary = {
            "pr_hash": pr_hash,
            "pr_number": pr["number"],
            "summary": summary_dict.summary,
            "key_points": summary_dict.key_points,
            "sentiment": summary_dict.sentiment
        }
        summary_collection.insert_one(summary)
        
        logger.info(f"Generated and stored summary for PR #{pr['number']}")
        return summary
    except Exception as e:
        logger.error(f"Error generating summary for PR #{pr['number']}: {str(e)}")
        return None

def summarize_prs() -> List[Dict[str, Any]]:
    prs = pr_collection.find()
    summaries = []
    for pr in prs:
        summary = generate_pr_summary(pr)
        if summary:
            pr_summary = {
                "pr_number": pr["number"],
                "summary": summary.get("summary", "No summary available"),
                "key_points": summary.get("key_points", []),
                "sentiment": summary.get("sentiment", "Unknown")
            }
            summaries.append(pr_summary)
        else:
            logger.warning(f"No summary generated for PR #{pr['number']}")
    
    return summaries

if __name__ == "__main__":
    results = summarize_prs()
    # print(json.dumps(results, indent=2))