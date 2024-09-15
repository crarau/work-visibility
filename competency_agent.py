import re
import json
from openai import OpenAI
from typing import Dict, Any

class CompetencyAgent:
    def __init__(self, competency_description: str, api_key: str):
        self.competency_description = competency_description
        self.client = OpenAI(api_key=api_key)

    def generate_prompt(self, pr_patch: str, pr_description: str, pr_link: str) -> str:
        return f"""
        Competency Description:
        {self.competency_description}

        PR Description:
        {pr_description}

        PR Patch:
        {pr_patch}

        PR Link:
        {pr_link}

        Determine if the PR relates to the competency. If it does, summarize the relevant parts starting with the PR title and name of the competency it relates to.

        Response format:
        {{
            "summary": "Summary"
        }}
        """

    def analyze_pr(self, pr_patch: str, pr_description: str, pr_link: str) -> Dict[str, Any]:
        prompt = self.generate_prompt(pr_patch, pr_description, pr_link)
        
        response = self.client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.0
        )
        
        try:
            result = json.loads(response.choices[0].message.content.strip())
            result["pr_link"] = pr_link
            # Ensure the summary is "-" if it doesn't relate to the competency
            if not result["summary"] or result["summary"].strip() == pr_description:
                result["summary"] = "-"
            return result
        except:
            return {"pr_link": pr_link, "summary": "-"}

