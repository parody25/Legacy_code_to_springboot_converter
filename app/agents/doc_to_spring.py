import json
from typing import List, Dict, Any

from app.agents.prompts import DOC_TO_SPRING_PROMPT
from app.clients.azure_openai_client import AzureLLMClient
from app.utils.json_utils import safe_json_list


class DocToSpringAgent:
    def __init__(self) -> None:
        self.client = AzureLLMClient()
        print("Initialized AzureLLMClient")

    def run(self, migration_doc: str, context_snippets: List[str]) -> List[Dict[str, str]]:
        print("Running DocToSpringAgent...")
        print(f"Received migration_doc (truncated to 6000 chars): {migration_doc[:6000]}")
        print(f"Received context_snippets (first 10): {context_snippets[:10]}")

        messages = [
            {"role": "system", "content": DOC_TO_SPRING_PROMPT},
            {"role": "user", "content": json.dumps({
                "migration_doc": migration_doc[:6000],
                "context": context_snippets[:10],
            })},
        ]
        print(f"Constructed messages: {messages}")

        raw = self.client.chat(messages)
        print(f"Raw response from AzureLLMClient: {raw}")
        files: List[Dict[str, str]] = safe_json_list(raw)
        print(f"Sanitized parsed files (len={len(files)}).")
        return files
