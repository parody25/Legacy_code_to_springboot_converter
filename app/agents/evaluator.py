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
from app.ingestion.structured_chunker import CodeStructure
import shutil


class EvaluatorAgent:
    def __init__(self) -> None:
        self.client = AzureLLMClient()

    def _analyze_legacy_code_structure(self, structures: List[CodeStructure]) -> Dict[str, Any]:
        """Analyze the structure and complexity of legacy code using structured chunks"""
        print("Analyzing legacy code structure using structured chunks...")
        
        # Count different types of structures
        classes = [s for s in structures if s.type == 'class']
        methods = [s for s in structures if s.type == 'method']
        interfaces = [s for s in structures if s.type == 'interface']
        enums = [s for s in structures if s.type == 'enum']
        
        # Calculate total code size
        total_code_size = sum(len(s.content) for s in structures)
        
        # Get unique files
        unique_files = set(s.file_path for s in structures)
        java_files = [f for f in unique_files if f.endswith('.java')]
        
        # Calculate complexity score
        complexity_score = self._calculate_complexity_score(structures)
        
        return {
            "total_files": len(unique_files),
            "java_files": len(java_files),
            "total_chunks": len(structures),
            "total_code_size": total_code_size,
            "classes_detected": len(classes),
            "methods_detected": len(methods),
            "interfaces_detected": len(interfaces),
            "enums_detected": len(enums),
            "complexity_score": complexity_score,
            "avg_dependencies": self._calculate_avg_dependencies(structures)
        }

    def _calculate_complexity_score(self, structures: List[CodeStructure]) -> float:
        """Calculate a complexity score based on structured code characteristics"""
        if not structures:
            return 0.0
            
        total_lines = sum(s.content.count('\n') for s in structures)
        total_methods = len([s for s in structures if s.type == 'method'])
        total_classes = len([s for s in structures if s.type == 'class'])
        total_dependencies = sum(len(s.dependencies) for s in structures)
        
        if total_lines == 0:
            return 0.0
            
        # Enhanced complexity metric
        method_density = (total_methods / total_lines) * 10 if total_lines > 0 else 0
        class_density = (total_classes / total_lines) * 5 if total_lines > 0 else 0
        dependency_complexity = (total_dependencies / len(structures)) * 2 if structures else 0
        
        complexity = method_density + class_density + dependency_complexity
        return min(complexity, 10.0)  # Cap at 10

    def _calculate_avg_dependencies(self, structures: List[CodeStructure]) -> float:
        """Calculate average dependencies per structure"""
        if not structures:
            return 0.0
        total_deps = sum(len(s.dependencies) for s in structures)
        return total_deps / len(structures)

    def run(self, migration_doc: str, structures: List[CodeStructure], project_dir: str) -> Dict[str, Any]:
        """Evaluate the quality of migration documentation against legacy code"""
        print("Starting documentation quality evaluation...")
        print(f"Number of legacy code structures: {len(structures)}")
        
        # 1. Legacy Code Analysis using structured chunks
        legacy_structure = self._analyze_legacy_code_structure(structures)
        
        # 2. Documentation Quality Assessment via LLM
        llm_messages = [
            {"role": "system", "content": EVALUATOR_GUIDE},
            {"role": "user", "content": json.dumps({
                "migration_documentation": migration_doc[:8000],
                "legacy_code_analysis": {
                    "structure": legacy_structure,
                    "code_analysis": {
                        "total_chunks": len(structures),
                        "total_code_size": legacy_structure["total_code_size"],
                        "classes_detected": legacy_structure["classes_detected"],
                        "methods_detected": legacy_structure["methods_detected"],
                        "interfaces_detected": legacy_structure["interfaces_detected"],
                        "enums_detected": legacy_structure["enums_detected"],
                        "complexity_score": legacy_structure["complexity_score"],
                        "avg_dependencies": legacy_structure["avg_dependencies"]
                    },
                    "sample_structures": [
                        {
                            "name": s.name,
                            "type": s.type,
                            "file_path": s.file_path,
                            "preview": s.content[:500],
                            "dependencies": s.dependencies
                        } 
                        for s in structures[:10]
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
                "code_analysis": {
                    "total_chunks": len(structures),
                    "total_code_size": legacy_structure["total_code_size"],
                    "classes_detected": legacy_structure["classes_detected"],
                    "methods_detected": legacy_structure["methods_detected"],
                    "interfaces_detected": legacy_structure["interfaces_detected"],
                    "enums_detected": legacy_structure["enums_detected"],
                    "complexity_score": legacy_structure["complexity_score"],
                    "avg_dependencies": legacy_structure["avg_dependencies"]
                }
            },
            "documentation_quality_assessment": llm_eval_json if llm_eval_json else None,
            "raw_llm_response": None if llm_eval_json else llm_eval_text,
            "summary": {
                "overall_status": "PASS",
                "critical_issues": 0,
                "recommendations": []
            }
        }
        
        # Add recommendations based on analysis
        if legacy_structure["complexity_score"] > 7.0:
            evaluation_report["summary"]["recommendations"].append("High complexity detected - consider refactoring before migration")
        
        if legacy_structure["total_code_size"] > 100000:
            evaluation_report["summary"]["recommendations"].append("Large codebase - consider incremental migration approach")
        
        if legacy_structure["classes_detected"] == 0:
            evaluation_report["summary"]["recommendations"].append("No classes detected - verify code structure")
        
        if legacy_structure["avg_dependencies"] > 5:
            evaluation_report["summary"]["recommendations"].append("High dependency complexity - plan migration order carefully")
        
        print("Documentation evaluation process completed.")
        return evaluation_report
