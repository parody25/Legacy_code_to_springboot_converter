import json
import re
from typing import Any, Dict, List, Tuple, Optional


def _extract_code_fence(text: str) -> str:
    # Try ```json ... ``` first
    fence = re.search(r"```json\s*([\s\S]*?)```", text, flags=re.IGNORECASE)
    if fence:
        return fence.group(1).strip()
    # Try any fenced block
    fence_any = re.search(r"```\s*([\s\S]*?)```", text)
    if fence_any:
        return fence_any.group(1).strip()
    return text


def _extract_braces(text: str) -> str:
    # Return the longest balanced {...} block
    start_positions: List[int] = [i for i, c in enumerate(text) if c == '{']
    if not start_positions:
        return text
    best: Tuple[int, int] | None = None
    for start in start_positions:
        depth = 0
        for j in range(start, len(text)):
            if text[j] == '{':
                depth += 1
            elif text[j] == '}':
                depth -= 1
                if depth == 0:
                    if best is None or (j - start) > (best[1] - best[0]):
                        best = (start, j + 1)
                    break
    if best is not None:
        return text[best[0]:best[1]]
    return text


def safe_json_list(text: str) -> List[Dict[str, Any]]:
    # Try direct list parse
    try:
        obj = json.loads(text)
        if isinstance(obj, list):
            return [x for x in obj if isinstance(x, dict)]
    except Exception:
        pass
    # Try fenced content
    fenced = _extract_code_fence(text)
    try:
        obj = json.loads(fenced)
        if isinstance(obj, list):
            return [x for x in obj if isinstance(x, dict)]
    except Exception:
        pass
    # Try brace extraction then list or object-to-list
    braced = _extract_braces(text)
    try:
        obj = json.loads(braced)
        if isinstance(obj, list):
            return [x for x in obj if isinstance(x, dict)]
        if isinstance(obj, dict):
            return [obj]
    except Exception:
        pass
    return []


def safe_json_object(text: str) -> Optional[Dict[str, Any]]:
    # Try direct object parse
    try:
        obj = json.loads(text)
        if isinstance(obj, dict):
            return obj
    except Exception:
        pass
    # Try fenced
    fenced = _extract_code_fence(text)
    try:
        obj = json.loads(fenced)
        if isinstance(obj, dict):
            return obj
    except Exception:
        pass
    # Try longest braced
    braced = _extract_braces(text)
    try:
        obj = json.loads(braced)
        if isinstance(obj, dict):
            return obj
    except Exception:
        pass
    return None


