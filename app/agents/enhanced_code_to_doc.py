import json
import time
from typing import List, Dict, Any
from app.ingestion.structured_chunker import CodeStructure
from app.analysis.dependency_graph import DependencyGraph, CodeSummary
from app.clients.azure_openai_client import AzureLLMClient
from app.config import settings
from app.agents.prompts import STRUCTURED_SUMMARY_PROMPT, CONTEXT_PRESERVING_DOC_PROMPT


class EnhancedCodeToDocumentAgent:
    """Enhanced agent that preserves business logic context through structured analysis"""
    
    def __init__(self):
        self.client = AzureLLMClient()
        self.dependency_graph = DependencyGraph()
        self.structured_summaries: Dict[str, CodeSummary] = {}
    
    def run(self, structures: List[CodeStructure]) -> str:
        """Generate comprehensive documentation with preserved business logic context"""
        print("Starting enhanced code-to-document conversion...")
        print(f"Processing {len(structures)} structural elements")
        
        # Step 1: Build dependency graph
        self.dependency_graph.build_graph(structures)
        
        # Step 2: Generate structured summaries for each element
        self._generate_structured_summaries(structures)
        
        # Step 3: Generate comprehensive documentation with context
        migration_doc = self._generate_context_preserving_documentation()
        
        # Step 4: Export knowledge base for future use
        self.dependency_graph.export_knowledge_base("data/workspace/knowledge_base.json")
        
        return migration_doc
    
    def _generate_structured_summaries(self, structures: List[CodeStructure]) -> None:
        """Generate structured summaries for each code element"""
        print("Generating structured summaries...")
        
        # Group structures by type for batch processing
        classes = [s for s in structures if s.type == 'class']
        methods = [s for s in structures if s.type == 'method']
        interfaces = [s for s in structures if s.type == 'interface']
        enums = [s for s in structures if s.type == 'enum']
        
        # Process classes first (they're the main components)
        for i, structure in enumerate(classes):
            print(f"Processing class {i+1}/{len(classes)}: {structure.name}")
            summary = self._generate_element_summary(structure)
            self.structured_summaries[structure.name] = summary
            self.dependency_graph.add_summary(summary)
            time.sleep(0.5)  # Rate limiting
        
        # Process methods
        for i, structure in enumerate(methods):
            print(f"Processing method {i+1}/{len(methods)}: {structure.name}")
            summary = self._generate_element_summary(structure)
            self.structured_summaries[structure.name] = summary
            self.dependency_graph.add_summary(summary)
            time.sleep(0.3)
        
        # Process interfaces
        for structure in interfaces:
            summary = self._generate_element_summary(structure)
            self.structured_summaries[structure.name] = summary
            self.dependency_graph.add_summary(summary)
        
        # Process enums
        for structure in enums:
            summary = self._generate_element_summary(structure)
            self.structured_summaries[structure.name] = summary
            self.dependency_graph.add_summary(summary)
        
        print(f"Generated {len(self.structured_summaries)} structured summaries")
    
    def _generate_element_summary(self, structure: CodeStructure) -> CodeSummary:
        """Generate a structured summary for a single code element"""
        # Get neighborhood context
        neighborhood = self.dependency_graph.get_neighborhood(structure.name, depth=1)
        neighborhood_context = []
        
        for neighbor_name in neighborhood:
            if neighbor_name in self.dependency_graph.nodes:
                neighbor = self.dependency_graph.nodes[neighbor_name]
                neighborhood_context.append({
                    'name': neighbor.name,
                    'type': neighbor.type,
                    'content': neighbor.content[:500]  # Truncate for context
                })
        
        # Prepare enhanced LLM prompt with more context
        messages = [
            {"role": "system", "content": STRUCTURED_SUMMARY_PROMPT},
            {"role": "user", "content": json.dumps({
                "element": {
                    "name": structure.name,
                    "type": structure.type,
                    "content": structure.content,
                    "file_path": structure.file_path,
                    "dependencies": structure.dependencies,
                    "modifiers": structure.modifiers or [],
                    "return_type": structure.return_type,
                    "parameters": structure.parameters or [],
                    "parent_class": structure.parent_class
                },
                "neighborhood_context": neighborhood_context[:5],  # Limit context size
                "analysis_instructions": {
                    "focus_on_business_logic": True,
                    "extract_all_validation_rules": True,
                    "identify_workflows_and_processes": True,
                    "capture_error_handling": True,
                    "analyze_data_transformations": True,
                    "identify_integration_points": True
                }
            })}
        ]
        
        # Get LLM response
        response = self.client.chat(messages)
        
        try:
            summary_data = json.loads(response)
            
            # Validate and enhance the summary data
            business_rules = summary_data.get('business_rules', [])
            if not business_rules or (len(business_rules) == 1 and business_rules[0] == 'None'):
                # Try to extract business rules from the code content
                business_rules = self._extract_business_rules_from_code(structure.content)
            
            inputs = summary_data.get('inputs', [])
            if not inputs or (len(inputs) == 1 and inputs[0] == 'None'):
                # Extract inputs from parameters and method signature
                inputs = self._extract_inputs_from_code(structure)
            
            outputs = summary_data.get('outputs', [])
            if not outputs or (len(outputs) == 1 and outputs[0] == 'None'):
                # Extract outputs from return type and method behavior
                outputs = self._extract_outputs_from_code(structure)
            
            return CodeSummary(
                name=structure.name,
                type=structure.type,
                file_path=structure.file_path,
                purpose=summary_data.get('purpose', f"{structure.type} {structure.name}"),
                inputs=inputs,
                outputs=outputs,
                business_rules=business_rules,
                dependencies=structure.dependencies,
                key_methods=summary_data.get('key_methods', []),
                complexity_score=summary_data.get('complexity_score', 0.0)
            )
        except json.JSONDecodeError:
            # Fallback summary with enhanced extraction
            business_rules = self._extract_business_rules_from_code(structure.content)
            inputs = self._extract_inputs_from_code(structure)
            outputs = self._extract_outputs_from_code(structure)
            
            return CodeSummary(
                name=structure.name,
                type=structure.type,
                file_path=structure.file_path,
                purpose=f"{structure.type} {structure.name}",
                inputs=inputs,
                outputs=outputs,
                business_rules=business_rules,
                dependencies=structure.dependencies,
                key_methods=[],
                complexity_score=0.0
            )
    
    def _extract_business_rules_from_code(self, content: str) -> List[str]:
        """Extract business rules from code content using pattern matching"""
        business_rules = []
        
        # Look for validation patterns
        if 'if' in content and ('null' in content or 'isEmpty' in content or 'length' in content):
            business_rules.append("Input validation and null checks")
        
        if 'throw' in content and 'Exception' in content:
            business_rules.append("Exception handling and error management")
        
        if 'return' in content and ('true' in content or 'false' in content):
            business_rules.append("Boolean logic and decision making")
        
        if 'for' in content or 'while' in content:
            business_rules.append("Iterative processing and data transformation")
        
        if 'new' in content and 'Date' in content:
            business_rules.append("Date/time processing")
        
        if 'String' in content and ('equals' in content or 'contains' in content):
            business_rules.append("String validation and processing")
        
        if 'Math.' in content or 'calculate' in content.lower():
            business_rules.append("Mathematical calculations and computations")
        
        if 'save' in content.lower() or 'update' in content.lower() or 'delete' in content.lower():
            business_rules.append("Data persistence operations")
        
        if 'log' in content.lower() or 'logger' in content.lower():
            business_rules.append("Logging and audit trail")
        
        return business_rules if business_rules else ["Basic business logic implementation"]
    
    def _extract_inputs_from_code(self, structure: CodeStructure) -> List[str]:
        """Extract inputs from code structure"""
        inputs = []
        
        # Add method parameters
        if structure.parameters:
            for param in structure.parameters:
                inputs.append(f"{param.get('type', 'Object')} {param.get('name', 'param')}")
        
        # Add dependencies as potential inputs
        for dep in structure.dependencies:
            if dep not in ['String', 'Integer', 'Boolean', 'Date', 'List', 'Map', 'Set']:
                inputs.append(f"{dep} dependency")
        
        return inputs if inputs else ["Standard input parameters"]
    
    def _extract_outputs_from_code(self, structure: CodeStructure) -> List[str]:
        """Extract outputs from code structure"""
        outputs = []
        
        # Add return type
        if structure.return_type and structure.return_type != 'void':
            outputs.append(f"{structure.return_type} return value")
        
        # Look for side effects in content
        content = structure.content.lower()
        if 'print' in content or 'system.out' in content:
            outputs.append("Console output")
        
        if 'log' in content or 'logger' in content:
            outputs.append("Logging output")
        
        if 'save' in content or 'update' in content or 'delete' in content:
            outputs.append("Database state changes")
        
        if 'throw' in content:
            outputs.append("Exception output")
        
        return outputs if outputs else ["Standard output"]
    
    def _generate_context_preserving_documentation(self) -> str:
        """Generate comprehensive documentation that preserves business logic context"""
        print("Generating context-preserving documentation...")
        
        # Get migration order (dependency-first)
        migration_order = self.dependency_graph.get_migration_order()
        
        # Get complexity metrics
        complexity_metrics = self.dependency_graph.get_complexity_metrics()
        
        # Prepare comprehensive context
        context_data = {
            "migration_order": migration_order,
            "complexity_metrics": complexity_metrics,
            "structured_summaries": {},
            "dependency_analysis": {}
        }
        
        # Add structured summaries
        for name, summary in self.structured_summaries.items():
            context_data["structured_summaries"][name] = {
                "purpose": summary.purpose,
                "business_rules": summary.business_rules,
                "inputs": summary.inputs,
                "outputs": summary.outputs,
                "dependencies": summary.dependencies,
                "complexity_score": summary.complexity_score
            }
        
        # Add dependency analysis for key components
        for name in migration_order[:10]:  # Top 10 components
            if name in self.dependency_graph.nodes:
                node = self.dependency_graph.nodes[name]
                context_data["dependency_analysis"][name] = {
                    "dependencies": node.dependencies,
                    "dependents": node.dependents,
                    "type": node.type,
                    "file_path": node.file_path
                }
        
        # Generate documentation with LLM
        messages = [
            {"role": "system", "content": CONTEXT_PRESERVING_DOC_PROMPT},
            {"role": "user", "content": json.dumps(context_data)}
        ]
        
        migration_doc = self.client.chat(messages)
        
        # Add metadata to the document
        metadata = {
            "total_components": len(self.structured_summaries),
            "migration_order": migration_order,
            "complexity_metrics": complexity_metrics,
            "knowledge_base_path": "data/workspace/knowledge_base.json"
        }
        
        full_document = f"""# Legacy Java to Spring Boot Migration Blueprint

## Metadata
- **Total Components**: {metadata['total_components']}
- **Migration Order**: {', '.join(metadata['migration_order'][:10])}...
- **Knowledge Base**: {metadata['knowledge_base_path']}

## Complexity Analysis
- **Total Nodes**: {complexity_metrics['total_nodes']}
- **Average Dependencies**: {complexity_metrics['avg_dependencies']:.2f}
- **Circular Dependencies**: {complexity_metrics['circular_dependencies']}
- **Root Nodes**: {complexity_metrics['root_nodes']}
- **Leaf Nodes**: {complexity_metrics['leaf_nodes']}

## Migration Documentation

{migration_doc}

## Component Summaries

"""
        
        # Add component summaries
        for name, summary in self.structured_summaries.items():
            full_document += f"""
### {summary.type.title()}: {name}
- **Purpose**: {summary.purpose}
- **Business Rules**: {', '.join(summary.business_rules) if summary.business_rules else 'None'}
- **Inputs**: {', '.join(summary.inputs) if summary.inputs else 'None'}
- **Outputs**: {', '.join(summary.outputs) if summary.outputs else 'None'}
- **Dependencies**: {', '.join(summary.dependencies) if summary.dependencies else 'None'}
- **Complexity Score**: {summary.complexity_score:.2f}

"""
        
        return full_document
    
    def get_migration_context(self, target_component: str) -> Dict[str, Any]:
        """Get comprehensive migration context for a specific component"""
        return self.dependency_graph.get_context_for_migration(target_component)
    
    def get_optimal_migration_order(self) -> List[str]:
        """Get the optimal order for migrating components"""
        return self.dependency_graph.get_migration_order()
    
    def export_knowledge_base(self, path: str) -> None:
        """Export the knowledge base"""
        self.dependency_graph.export_knowledge_base(path)
