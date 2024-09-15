from flask import Flask, render_template, request, jsonify
from pymongo import MongoClient
import os
from dotenv import load_dotenv
import random

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
    if pr_collection is None:
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
        
        competencies = [
            "Writing code", "Testing", "Debugging", "Observability",
            "Understanding Code", "Software Architecture", "Security"
        ]
        
        return render_template('dashboard.html', prs=list(prs), competencies=competencies)
    except Exception as e:
        print(f"Error fetching data: {e}")
        return "Error fetching data", 500

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

if __name__ == '__main__':
    app.run(debug=True)
