import json
import os
import subprocess
import tempfile
from typing import List, Dict, Any, Tuple

import javalang  # type: ignore
from app.agents.prompts import EVALUATOR_GUIDE
from app.clients.azure_openai_client import AzureLLMClient
from app.config import settings
from app.utils.json_utils import safe_json_object
import shutil


class EvaluatorAgent:
    def __init__(self) -> None:
        self.client = AzureLLMClient()

    def _syntax_check_legacy_java(self, chunks: List[Tuple[str, int, str]]) -> List[Dict[str, Any]]:
        """Check syntax of legacy Java code chunks"""
        print("Starting syntax check for legacy Java code chunks...")
        results: List[Dict[str, Any]] = []
        
        for i, (path, idx, text) in enumerate(chunks):
            if not path.endswith('.java'):
                continue
                
            try:
                print(f"Checking syntax for chunk {i+1}/{len(chunks)}: {path}")
                list(javalang.parse.parse(text))
                results.append({
                    "syntax": True, 
                    "file": path, 
                    "chunk_index": idx,
                    "chunk_size": len(text)
                })
                print("Syntax check passed.")
            except Exception as e:
                print(f"Syntax check failed with error: {e}")
                results.append({
                    "syntax": False, 
                    "error": str(e), 
                    "file": path, 
                    "chunk_index": idx,
                    "chunk_size": len(text)
                })
        print("Completed legacy code syntax checks.")
        return results

    def _analyze_legacy_code_structure(self, chunks: List[Tuple[str, int, str]]) -> Dict[str, Any]:
        """Analyze the structure and complexity of legacy code"""
        print("Analyzing legacy code structure...")
        
        java_files = [path for path, _, _ in chunks if path.endswith('.java')]
        total_chunks = len(chunks)
        total_code_size = sum(len(text) for _, _, text in chunks)
        
        # Extract class names and basic structure
        classes = []
        methods = []
        
        for path, idx, text in chunks:
            if not path.endswith('.java'):
                continue
                
            try:
                tree = javalang.parse.parse(text)
                for path_obj, node in tree:
                    if isinstance(node, javalang.tree.ClassDeclaration):
                        classes.append({
                            "name": node.name,
                            "file": path,
                            "chunk": idx
                        })
                    elif isinstance(node, javalang.tree.MethodDeclaration):
                        methods.append({
                            "name": node.name,
                            "file": path,
                            "chunk": idx
                        })
            except Exception:
                # Skip chunks that can't be parsed
                continue
        
        return {
            "total_files": len(set(path for path, _, _ in chunks)),
            "java_files": len(java_files),
            "total_chunks": total_chunks,
            "total_code_size": total_code_size,
            "classes_detected": len(classes),
            "methods_detected": len(methods),
            "complexity_score": self._calculate_complexity_score(chunks)
        }

    def _calculate_complexity_score(self, chunks: List[Tuple[str, int, str]]) -> float:
        """Calculate a simple complexity score based on code characteristics"""
        total_lines = sum(text.count('\n') for _, _, text in chunks)
        total_methods = sum(text.count('public ') + text.count('private ') + text.count('protected ') for _, _, text in chunks)
        total_classes = sum(text.count('class ') for _, _, text in chunks)
        
        if total_lines == 0:
            return 0.0
            
        # Simple complexity metric: methods per line + classes per line
        complexity = (total_methods / total_lines) * 10 + (total_classes / total_lines) * 5
        return min(complexity, 10.0)  # Cap at 10

    def run(self, migration_doc: str, chunks: List[Tuple[str, int, str]], project_dir: str) -> Dict[str, Any]:
        """Evaluate the quality of migration documentation against legacy code"""
        print("Starting documentation quality evaluation...")
        print(f"Number of legacy code chunks: {len(chunks)}")
        
        # 1. Legacy Code Analysis
        legacy_structure = self._analyze_legacy_code_structure(chunks)
        syntax_results = self._syntax_check_legacy_java(chunks)
        
        # 2. Documentation Quality Assessment via LLM
        llm_messages = [
            {"role": "system", "content": EVALUATOR_GUIDE},
            {"role": "user", "content": json.dumps({
                "migration_documentation": migration_doc[:8000],
                "legacy_code_analysis": {
                    "structure": legacy_structure,
                    "syntax_validation": {
                        "total_chunks": len(chunks),
                        "valid_chunks": len([r for r in syntax_results if r.get("syntax", False)]),
                        "invalid_chunks": len([r for r in syntax_results if not r.get("syntax", False)]),
                        "details": syntax_results
                    },
                    "sample_code_chunks": [
                        {"path": path, "chunk": idx, "preview": text[:500]} 
                        for path, idx, text in chunks[:10]
                    ]
                }
            })}
        ]
        
        print("Sending documentation quality assessment to LLM...")
        llm_eval_text = self.client.chat(llm_messages)
        print("LLM evaluation completed.")
        
        # Parse LLM response
        llm_eval_json = safe_json_object(llm_eval_text)
        
        # Compile final evaluation report
        evaluation_report = {
            "legacy_code_analysis": {
                "structure": legacy_structure,
                "syntax_validation": {
                    "total_chunks": len(chunks),
                    "valid_chunks": len([r for r in syntax_results if r.get("syntax", False)]),
                    "invalid_chunks": len([r for r in syntax_results if not r.get("syntax", False)]),
                    "details": syntax_results
                }
            },
            "documentation_quality_assessment": llm_eval_json if llm_eval_json else None,
            "raw_llm_response": None if llm_eval_json else llm_eval_text,
            "summary": {
                "overall_status": "PASS" if all(r.get("syntax", False) for r in syntax_results) else "FAIL",
                "critical_issues": len([r for r in syntax_results if not r.get("syntax", False)]),
                "recommendations": []
            }
        }
        
        # Add recommendations based on analysis
        if any(not r.get("syntax", False) for r in syntax_results):
            evaluation_report["summary"]["recommendations"].append("Fix syntax errors in legacy code before migration")
        
        if legacy_structure["complexity_score"] > 7.0:
            evaluation_report["summary"]["recommendations"].append("High complexity detected - consider refactoring before migration")
        
        if legacy_structure["total_code_size"] > 100000:
            evaluation_report["summary"]["recommendations"].append("Large codebase - consider incremental migration approach")
        
        print("Documentation evaluation process completed.")
        return evaluation_report
