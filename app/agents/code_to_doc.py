import json
import time
from typing import List, Tuple, Dict, Any

from app.agents.prompts import CODE_TO_DOC_PROMPT, CODE_TO_DOC_REDUCE_PROMPT
from app.clients.azure_openai_client import AzureLLMClient
#from azure.core.exceptions import ServiceResponseError, HttpResponseError

class CodeToDocumentAgent:
    def __init__(self) -> None:
        self.client = AzureLLMClient()
        self.map_batch_size = 15
        self.reduce_batch_size = 5 # Batch size for the new hierarchical reduction

    def run(self, chunks: List[Tuple[str, int, str]]) -> str:
        """
        Runs the full map-reduce pipeline with a hierarchical reduction step.
        """
        print("Starting the document generation process (map phase)...")
        mini_summaries = self._map_phase(chunks)

        print("Starting hierarchical reduce phase to unify mini summaries...")
        final_doc = self._hierarchical_reduce(mini_summaries)

        print("Document generation completed (single unified doc produced).")
        return final_doc

    def _map_phase(self, chunks: List[Tuple[str, int, str]]) -> List[Dict[str, Any]]:
        """
        Processes chunks in batches and generates mini-summaries.
        Includes a small delay between batches to mitigate rate limits.
        """
        mini_summaries: List[Dict[str, Any]] = []
        batch: List[Dict[str, Any]] = []
        
        for i, (path, idx, text) in enumerate(chunks):
            print(f"Processing chunk: path={path}, idx={idx}, text_length={len(text)}")
            batch.append({"path": path, "chunk": idx, "text": text[:2000]})
            
            if len(batch) >= self.map_batch_size:
                print(f"Batch size reached {self.map_batch_size}. Sending batch to client: {len(batch)} items")
                messages = [
                    {"role": "system", "content": CODE_TO_DOC_PROMPT},
                    {"role": "user", "content": json.dumps(batch)},
                ]
                out = self.client.chat(messages)
                mini_summaries.append({"doc": out})
                batch = []
                # Introduce a small, deliberate pause to prevent rate limiting
                time.sleep(1) 
        
        # Process the final remaining batch
        if batch:
            print(f"Processing remaining batch: {len(batch)} items")
            messages = [
                {"role": "system", "content": CODE_TO_DOC_PROMPT},
                {"role": "user", "content": json.dumps(batch)},
            ]
            out = self.client.chat(messages)
            mini_summaries.append({"doc": out})

        return mini_summaries

    def _hierarchical_reduce(self, summaries: List[Dict[str, Any]]) -> str:
        """
        Iteratively reduces summaries in batches until a single document remains.
        """
        if not summaries:
            return ""

        current_summaries = summaries
        
        while len(current_summaries) > 1:
            next_summaries = []
            print(f"Reducing {len(current_summaries)} summaries in batches of {self.reduce_batch_size}...")
            
            for i in range(0, len(current_summaries), self.reduce_batch_size):
                batch_to_reduce = current_summaries[i:i + self.reduce_batch_size]
                
                # Create a list of the 'doc' strings from the batch
                batch_docs = [s['doc'] for s in batch_to_reduce]
                
                messages = [
                    {"role": "system", "content": CODE_TO_DOC_REDUCE_PROMPT},
                    {"role": "user", "content": json.dumps({"batch": batch_docs})},
                ]
                
                try:
                    out = self.client.chat(messages)
                    next_summaries.append({"doc": out})
                #except (ServiceResponseError, HttpResponseError) as e:
                except Exception as e:
                    print(f"Error during reduction step: {e}. Retrying after a pause...")
                    time.sleep(10) # Wait longer on error
                    out = self.client.chat(messages)
                    next_summaries.append({"doc": out})

                # Introduce a small delay between reduction batches
                time.sleep(1)

            current_summaries = next_summaries

        return current_summaries[0]['doc']
