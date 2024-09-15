from flask import Flask, render_template, request, jsonify
from pymongo import MongoClient
import os
from dotenv import load_dotenv
import random
from bson import ObjectId

load_dotenv()

app = Flask(__name__)

# MongoDB connection
MONGO_URI = os.getenv("MONGO_URI")
client = None
db = None
pr_collection = None

try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    client.server_info()  # This will raise an exception if connection fails
    db = client.github_prs
    pr_collection = db.pull_requests
except Exception as e:
    print(f"Failed to connect to MongoDB: {e}")

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
        
        # Default competencies
        default_competencies = {
            "Writing_code": "Consistently writes production-ready code that is easily testable, easily understood by other developers, and accounts for edge cases and errors. Understands when it is appropriate to leave comments, but biases towards self-documenting code.",
            "Testing": "Understands the testing pyramid, and writes unit tests as well as higher level tests in accordance with it. Always writes tests to handle expected edge cases and errors gracefully, as well as happy paths.",
            "Debugging": "Proficient at using systematic debugging to diagnose all issues located to a single service. Uses systematic debugging to diagnose cross service issues, sometimes with help from more senior engineers.",
            "Observability": "Is aware of the organization's monitoring philosophy. Helps tune and change the monitoring on their team accordingly. Is aware of the operational data for their team's domain and uses it as a basis for suggesting stability and performance improvements.",
            "Understanding_Code": "Understands their team's domain at a high level and can gather sufficient context to work productively within it. Has expertise in a portion of their team's domain.",
            "Software_Architecture": "Consistently designs code that is aligned with the overall service architecture. Utilizes abstractions and code isolation effectively.",
            "Security": "Approaches all engineering work with a security lens. Actively looks for security vulnerabilities both in the code and when providing peer reviews."
        }
        
        # Fetch user's competencies from the database
        user_id = generate_github_user_id()
        user_matrix = db.competency_matrices.find_one({"user_id": user_id})
        
        if user_matrix and "competencies" in user_matrix:
            competency_ids = user_matrix["competencies"]
            competencies = {}
            for comp_id in competency_ids:
                comp = db.competencies.find_one({"_id": ObjectId(comp_id)})
                if comp:
                    competencies[comp["name"]] = comp["description"]
        else:
            competencies = default_competencies
        
        return render_template('dashboard.html', prs=list(prs), competencies=competencies)
    except Exception as e:
        import traceback
        error_message = f"Error fetching data: {str(e)}\n{traceback.format_exc()}"
        print(error_message)
        return error_message, 500

@app.route('/competency-matrix', methods=['GET', 'POST'])
def competency_matrix():
    if request.method == 'POST':
        user_id = generate_github_user_id()  # Implement this function
        payload = request.form.to_dict()
        
        competencies = []
        for key, value in payload.items():
            competency = {
                "name": key,
                "description": value,
                "user_id": user_id
            }
            competency_id = db.competencies.insert_one(competency).inserted_id
            competencies.append(str(competency_id))
        
        user_matrix = {
            "user_id": user_id,
            "competencies": competencies
        }
        db.competency_matrices.insert_one(user_matrix)
        
        return jsonify({"success": True, "user_id": user_id})

    competencies = [
        "Writing code", "Testing", "Debugging", "Observability",
        "Understanding Code", "Software Architecture", "Security"
    ]
    return render_template('competency_matrix.html', competencies=competencies)

def generate_github_user_id():
    # Return the static user ID
    return 'oa6xgic4mf'

@app.route('/api/joke')
def get_joke():
    jokes = [
        "Why do programmers prefer dark mode? Because light attracts bugs!",
        "Why did the developer go broke? Because he used up all his cache!",
        "Why do programmers always mix up Halloween and Christmas? Because Oct 31 == Dec 25!",
        "Why was the JavaScript developer sad? Because he didn't Node how to Express himself!",
        "Why did the developer quit his job? Because he didn't get arrays!"
    ]
    return jsonify({"joke": random.choice(jokes)})

@app.route('/save-competencies', methods=['POST'])
def save_competencies():
    if db is None:
        return jsonify({"success": False, "error": "Database connection error"}), 500
    
    try:
        competencies = request.json
        user_id = generate_github_user_id()  # You may want to replace this with actual user authentication
        
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

if __name__ == '__main__':
    app.run(debug=True)
