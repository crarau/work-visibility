from flask import Flask, render_template
from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client.github_prs
pr_collection = db.pull_requests

app = Flask(__name__)

@app.route('/')
def index():
    prs = pr_collection.find({}, {
        "number": 1,
        "title": 1,
        "user": 1,
        "state": 1,
        "created_at": 1,
        "updated_at": 1,
        "_id": 0
    }).sort("updated_at", -1).limit(50)
    
    return render_template('index.html', prs=prs)

if __name__ == '__main__':
    app.run(debug=True)
