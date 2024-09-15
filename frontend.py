from flask import Flask, render_template, request, jsonify
from pymongo import MongoClient
import os
from dotenv import load_dotenv
import random
from bson import ObjectId
import requests
import json
from datetime import datetime, timedelta, timezone
from competency_agent import CompetencyAgent  # Ensure this import
import uuid

load_dotenv()

app = Flask(__name__)

# GitHub API settings
GITHUB_API_URL = "https://api.github.com"
REPO_OWNER = "openai"
REPO_NAME = "openai-python"

# Get the tokens from the .env file
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
MONGO_URI = os.getenv("MONGO_URI")

headers = {}
if GITHUB_TOKEN:
    headers["Authorization"] = f"token {GITHUB_TOKEN}"

# MongoDB connection
client = MongoClient(MONGO_URI)
db = client.github_prs
pr_collection = db.pull_requests
competencies_collection = db.competencies
agent_responses_collection = db.agent_responses
agent_logs_collection = db.agent_logs

@app.route('/')
def index():
    if pr_collection is None or db is None:
        return "Database connection error", 500
    
    try:
        # Filter PRs for RobertCraigie
        prs = pr_collection.find(
            {"user": "RobertCraigie"},
            {
                "number": 1,
                "title": 1,
                "user": 1,
                "state": 1,
                "_id": 0
            }
        ).sort("updated_at", -1).limit(50)
        
        # Fetch user's competencies from the database
        user_id = generate_github_user_id()
        user_matrix = db.competency_matrices.find_one({"user_id": user_id})
        
        if user_matrix and "competencies" in user_matrix:
            competencies = user_matrix["competencies"]
        else:
            # Use default competencies if no user-specific competencies are found
            competencies = {
                "Writing_code": "Consistently writes production-ready code that is easily testable, easily understood by other developers, and accounts for edge cases and errors. Understands when it is appropriate to leave comments, but biases towards self-documenting code.",
                "Testing": "Understands the testing pyramid, and writes unit tests as well as higher level tests in accordance with it. Always writes tests to handle expected edge cases and errors gracefully, as well as happy paths.",
                "Debugging": "Proficient at using systematic debugging to diagnose all issues located to a single service. Uses systematic debugging to diagnose cross service issues, sometimes with help from more senior engineers.",
                "Observability": "Is aware of the organization's monitoring philosophy. Helps tune and change the monitoring on their team accordingly. Is aware of the operational data for their team's domain and uses it as a basis for suggesting stability and performance improvements.",
                "Understanding_Code": "Understands their team's domain at a high level and can gather sufficient context to work productively within it. Has expertise in a portion of their team's domain.",
                "Software_Architecture": "Consistently designs code that is aligned with the overall service architecture. Utilizes abstractions and code isolation effectively.",
                "Security": "Approaches all engineering work with a security lens. Actively looks for security vulnerabilities both in the code and when providing peer reviews."
            }
        
        return render_template('dashboard.html', prs=list(prs), competencies=competencies)
    except Exception as e:
        import traceback
        error_message = f"Error fetching data: {str(e)}\n{traceback.format_exc()}"
        print(error_message)
        return error_message, 500

@app.route('/run_agents', methods=['POST'])
def run_agents():
    call_id = str(uuid.uuid4())
    agent_logs_collection.insert_one({
        "call_id": call_id,
        "timestamp": datetime.utcnow(),
        "status": "started",
        "message": "Agent run initiated."
    })

    try:
        total_prs = pr_collection.count_documents({})
        total_competencies = competencies_collection.count_documents({})
        
        agent_logs_collection.insert_one({
            "call_id": call_id,
            "timestamp": datetime.utcnow(),
            "status": "info",
            "message": f"Processing {total_prs} PRs and {total_competencies} competencies."
        })

        prs = pr_collection.find()
        competencies = competencies_collection.find()

        for pr in prs:
            pr_number = pr.get('number')
            pr_description = pr.get('body', '')
            pr_patch = pr.get('patch', '')
            pr_link = f"https://github.com/{REPO_OWNER}/{REPO_NAME}/pull/{pr_number}"

            agent_logs_collection.insert_one({
                "call_id": call_id,
                "timestamp": datetime.utcnow(),
                "status": "info",
                "message": f"Analyzing PR #{pr_number}."
            })

            competencies.rewind()
            for competency in competencies:
                competency_name = competency.get('name')
                competency_description = competency.get('description')

                agent_logs_collection.insert_one({
                    "call_id": call_id,
                    "timestamp": datetime.utcnow(),
                    "status": "info",
                    "message": f"Evaluating competency '{competency_name}' for PR #{pr_number}."
                })

                agent = CompetencyAgent(competency_description)
                prompt = agent.generate_prompt(pr_patch, pr_description, pr_link)
                result = agent.analyze_pr(pr_patch, pr_description, pr_link)

                agent_responses_collection.insert_one({
                    "call_id": call_id,
                    "pr_number": pr_number,
                    "competency_name": competency_name,
                    "summary": result.get("summary"),
                    "pr_link": pr_link,
                    "pr_description": pr_description,
                    "pr_patch": pr_patch,
                    "competency_description": competency_description,
                    "prompt": prompt,
                    "timestamp": datetime.utcnow()
                })

                agent_logs_collection.insert_one({
                    "call_id": call_id,
                    "timestamp": datetime.utcnow(),
                    "status": "info",
                    "message": f"Stored response for competency '{competency_name}' and PR #{pr_number}."
                })

        agent_logs_collection.insert_one({
            "call_id": call_id,
            "timestamp": datetime.utcnow(),
            "status": "completed",
            "message": "All agents have been processed successfully."
        })

        return jsonify({"success": True, "call_id": call_id, "message": "Agents processed successfully."}), 200

    except Exception as e:
        agent_logs_collection.insert_one({
            "call_id": call_id,
            "timestamp": datetime.utcnow(),
            "status": "error",
            "message": f"Error during agent processing: {str(e)}"
        })
        return jsonify({"success": False, "call_id": call_id, "error": str(e)}), 500

@app.route('/agent_logs/<call_id>', methods=['GET'])
def get_agent_logs(call_id):
    logs = list(agent_logs_collection.find({"call_id": call_id}).sort("timestamp", 1))
    for log in logs:
        log["_id"] = str(log["_id"])
    return jsonify({"logs": logs}), 200

@app.route('/agent_responses/<call_id>', methods=['GET'])
def get_agent_responses(call_id):
    responses = list(agent_responses_collection.find({"call_id": call_id}))
    for response in responses:
        response["_id"] = str(response["_id"])
    return jsonify({"responses": responses}), 200

@app.route('/save-competencies', methods=['POST'])
def save_competencies():
    if db is None:
        return jsonify({"success": False, "error": "Database connection error"}), 500
    
    try:
        competencies = request.json
        user_id = generate_github_user_id()
        
        # Update or insert the competencies for the user
        db.competency_matrices.update_one(
            {"user_id": user_id},
            {"$set": {"competencies": competencies}},
            upsert=True
        )
        
        return jsonify({"success": True})
    except Exception as e:
        print(f"Error saving competencies: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

def generate_github_user_id():
    # Return the static user ID
    return 'oa6xgic4mf'

if __name__ == '__main__':
    app.run(debug=True)
