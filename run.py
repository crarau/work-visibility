import requests
import json
from datetime import datetime, timedelta, timezone
import os
from dotenv import load_dotenv
from pymongo import MongoClient

# Load environment variables from .env file
load_dotenv()

# GitHub API settings
GITHUB_API_URL = "https://api.github.com"
REPO_OWNER = "openai"  # Replace with the actual owner
REPO_NAME = "openai-python"    # Replace with the actual repository name

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

# https://github.com/openai/openai-python

# The fetch_recent_merged_prs, fetch_pr_comments, fetch_pr_details, and fetch_pr_patch functions remain unchanged

def fetch_recent_merged_prs(from_date, to_date):
    url = f"{GITHUB_API_URL}/repos/{REPO_OWNER}/{REPO_NAME}/pulls"
    params = {
        "state": "all",
        "sort": "updated",
        "direction": "desc",
        "per_page": 100,
    }
    
    params["since"] = from_date.isoformat()

    all_prs = []

    while True:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        prs = response.json()
        
        if not prs:
            break

        # Filter PRs based on the to_date
        filtered_prs = [pr for pr in prs if datetime.fromisoformat(pr['updated_at'].replace('Z', '+00:00')) <= to_date]
        all_prs.extend(filtered_prs)

        if 'next' in response.links and datetime.fromisoformat(prs[-1]['updated_at'].replace('Z', '+00:00')) > from_date:
            url = response.links['next']['url']
        else:
            break

    return all_prs

def fetch_pr_comments(pr_number):
    url = f"{GITHUB_API_URL}/repos/{REPO_OWNER}/{REPO_NAME}/pulls/{pr_number}/comments"
    all_comments = []

    while True:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        comments = response.json()
        all_comments.extend(comments)

        if 'next' in response.links:
            url = response.links['next']['url']
        else:
            break

    return all_comments

def fetch_pr_details(pr_number):
    url = f"{GITHUB_API_URL}/repos/{REPO_OWNER}/{REPO_NAME}/pulls/{pr_number}"
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()

def fetch_pr_patch(pr_number):
    url = f"{GITHUB_API_URL}/repos/{REPO_OWNER}/{REPO_NAME}/pulls/{pr_number}"
    headers_with_patch = headers.copy()
    headers_with_patch["Accept"] = "application/vnd.github.v3.patch"
    response = requests.get(url, headers=headers_with_patch)
    response.raise_for_status()
    return response.text

def get_last_update_time():
    most_recent_pr = pr_collection.find_one(sort=[("updated_at", -1)])
    if most_recent_pr and "updated_at" in most_recent_pr:
        return most_recent_pr["updated_at"]
    else:
        # If no PRs exist or if 'updated_at' is missing, return None
        return None

def main():
    to_date = datetime.now(timezone.utc)
    from_date = to_date - timedelta(days=30)
    
    prs = fetch_recent_merged_prs(from_date, to_date)
    print(f"Fetched {len(prs)} PRs updated between {from_date.date()} and {to_date.date()}.")

    for pr in prs:
        # Check if PR exists and if it has been updated
        existing_pr = pr_collection.find_one({"number": pr['number']})
        if existing_pr and existing_pr.get('updated_at') == pr['updated_at']:
            print(f"No changes for PR #{pr['number']}")
            continue

        # Fetch additional details only if PR is new or updated
        pr_details = fetch_pr_details(pr['number'])
        pr_patch = fetch_pr_patch(pr['number'])
        pr_info = {
            "number": pr['number'],
            "title": pr['title'],
            "created_at": pr['created_at'],
            "merged_at": pr['merged_at'],
            "updated_at": pr['updated_at'],
            "user": pr['user']['login'],
            "body": pr['body'],
            "comments": fetch_pr_comments(pr['number']),
            "additions": pr_details['additions'],
            "deletions": pr_details['deletions'],
            "changed_files": pr_details['changed_files'],
            "patch": pr_patch,
            "state": pr['state']
        }
        
        # Insert or update the PR in MongoDB
        result = pr_collection.update_one(
            {"number": pr['number']},
            {"$set": pr_info},
            upsert=True
        )
        
        if result.modified_count > 0:
            print(f"Updated data for PR #{pr['number']} in MongoDB")
        elif result.upserted_id:
            print(f"Inserted new data for PR #{pr['number']} in MongoDB")

    print("PR data has been updated in MongoDB")

if __name__ == "__main__":
    main()