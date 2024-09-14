import requests
import json
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# GitHub API settings
GITHUB_API_URL = "https://api.github.com"
REPO_OWNER = "openai"  # Replace with the actual owner
REPO_NAME = "openai-python"    # Replace with the actual repository name

# https://github.com/openai/openai-python

# Get the token from the .env file
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

headers = {}
if GITHUB_TOKEN:
    headers["Authorization"] = f"token {GITHUB_TOKEN}"

def fetch_recent_merged_prs():
    url = f"{GITHUB_API_URL}/repos/{REPO_OWNER}/{REPO_NAME}/pulls"
    one_month_ago = (datetime.now() - timedelta(days=7)).isoformat()
    params = {
        "state": "closed",
        "sort": "updated",
        "direction": "desc",
        "per_page": 100,
    }
    all_prs = []

    while True:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        prs = response.json()
        
        if not prs:
            break

        for pr in prs:
            if pr['merged_at'] and pr['merged_at'] > one_month_ago:
                all_prs.append(pr)
            elif pr['updated_at'] < one_month_ago:
                return all_prs  # Stop if we've gone past our time window

        if 'next' in response.links:
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

def main():
    prs = fetch_recent_merged_prs()
    print(f"Fetched {len(prs)} merged PRs from the last month.")

    pr_data = []
    for pr in prs:
        pr_details = fetch_pr_details(pr['number'])
        pr_patch = fetch_pr_patch(pr['number'])
        pr_info = {
            "number": pr['number'],
            "title": pr['title'],
            "created_at": pr['created_at'],
            "merged_at": pr['merged_at'],
            "user": pr['user']['login'],
            "body": pr['body'],
            "comments": fetch_pr_comments(pr['number']),
            "additions": pr_details['additions'],
            "deletions": pr_details['deletions'],
            "changed_files": pr_details['changed_files'],
            "patch": pr_patch
        }
        pr_data.append(pr_info)
        print(f"Fetched data for PR #{pr['number']}")

    output_file = "recent_merged_prs_with_comments.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(pr_data, f, ensure_ascii=False, indent=2)

    print(f"Merged PR data with comments has been saved to {output_file}")

if __name__ == "__main__":
    main()