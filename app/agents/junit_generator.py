import json
from typing import List, Dict

from app.agents.prompts import JUNIT_PROMPT
from app.clients.azure_openai_client import AzureLLMClient
from app.utils.json_utils import safe_json_list


class JUnitGeneratorAgent:
    def __init__(self) -> None:
        self.client = AzureLLMClient()

    def run(self, spring_files: List[Dict[str, str]]) -> List[Dict[str, str]]:
        print("Starting JUnitGeneratorAgent.run()")
        print(f"Received {len(spring_files)} spring files")

        context = [{"path": f["path"], "content": f["content"][:2000]} for f in spring_files[:20]]
        print(f"Context prepared with {len(context)} files")

        messages = [
            {"role": "system", "content": JUNIT_PROMPT},
            {"role": "user", "content": json.dumps(context)},
        ]
        print("Messages prepared for Azure LLM Client")

        raw = self.client.chat(messages)
        print("Raw response received from Azure LLM Client")
        print(f"Raw response: {raw[:500]}")  # Print first 500 characters for debugging

        files: List[Dict[str, str]] = safe_json_list(raw)
        print(f"Sanitized parsed files (len={len(files)}). Returning generated files")
        return files
