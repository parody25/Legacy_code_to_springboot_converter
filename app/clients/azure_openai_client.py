import os
import re
import json
from dotenv import load_dotenv
from typing import List, Dict, Any
from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

load_dotenv()  # Load variables from .env


def sanitize_and_parse_json(raw_response: str) -> Any:
    """
    Clean LLM response and parse it into JSON.
    Handles cases where response contains ```json ... ``` fences.
    """
    # Remove Markdown fences like ```json ... ```
    cleaned = re.sub(r"^```(?:json)?|```$", "", raw_response.strip(), flags=re.MULTILINE)

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse JSON from LLM response: {e}\nRaw output:\n{raw_response}")


class AzureLLMClient:
    def __init__(self) -> None:
        api_key = os.getenv("AZURE_OPENAI_API_KEY")
        api_version = os.getenv("AZURE_OPENAI_API_VERSION")
        endpoint = os.getenv("AZURE_OPENAI_ENDPOINT").rstrip("/")

        # Deployment ID (must match Azure portal deployment name)
        self.chat_deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT")

        # Single client for chat
        self.chat_client = OpenAI(
            api_key=api_key,
            base_url=f"{endpoint}/openai/deployments/{self.chat_deployment}",
            default_query={"api-version": api_version},
            default_headers={"api-key": api_key},
        )

    @retry(stop=stop_after_attempt(6), wait=wait_exponential(min=1, max=30))
    def chat(self, messages: List[Dict[str, str]], temperature: float = 0.2, as_json: bool = False) -> Any:
        """
        Call Azure OpenAI chat completion.
        If as_json=True, attempts to sanitize and parse the response into JSON.
        """
        response = self.chat_client.chat.completions.create(
            model=self.chat_deployment,  # must be deployment ID
            messages=messages,
            temperature=temperature,
        )

        raw_output = response.choices[0].message.content or ""

        if as_json:
            return sanitize_and_parse_json(raw_output)
        return raw_output
