import re
from typing import Dict, Any
from langchain_openai import OpenAI

class CompetencyAgent:
    def __init__(self, competency_description: str):
        self.competency_description = competency_description
        self.llm = OpenAI(temperature=0.0)  # Set temperature to 0 for deterministic output

    def analyze_pr(self, pr_patch: str, pr_description: str, pr_link: str) -> Dict[str, Any]:
        prompt = f"""
        Competency Description:
        {self.competency_description}

        PR Description:
        {pr_description}

        PR Patch:
        {pr_patch}

        Determine if the PR relates to the competency. If it does, summarize the relevant parts. If not, return exactly "-" (a single dash).

        Response format:
        {{
            "summary": "Summary or -"
        }}
        """

        response = self.llm.invoke(prompt)
        try:
            result = eval(response.strip())
            result["pr_link"] = pr_link
            # Ensure the summary is "-" if it doesn't relate to the competency
            if not result["summary"] or result["summary"].strip() == pr_description:
                result["summary"] = "-"
            return result
        except:
            return {"pr_link": pr_link, "summary": "-"}

