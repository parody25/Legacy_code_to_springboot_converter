import json
import os
from typing import Dict, List, Set, Any, Optional
from collections import defaultdict, deque
from dataclasses import dataclass, asdict
from app.ingestion.structured_chunker import CodeStructure


@dataclass
class DependencyNode:
    """Represents a node in the dependency graph"""
    name: str
    type: str  # 'class', 'interface', 'method', 'enum', 'annotation', 'constant'
    file_path: str
    dependencies: List[str]  # Names of dependencies
    dependents: List[str]  # Names of classes that depend on this
    content: str
    metadata: Dict[str, Any]  # Additional metadata like modifiers, parameters, etc.


@dataclass
class CodeSummary:
    """Structured summary of a code element"""
    name: str
    type: str
    file_path: str
    purpose: str
    inputs: List[str]
    outputs: List[str]
    business_rules: List[str]
    dependencies: List[str]
    key_methods: List[str]
    complexity_score: float


class DependencyGraph:
    """Builds and manages a dependency graph of code structures"""
    
    def __init__(self):
        self.nodes: Dict[str, DependencyNode] = {}
        self.summaries: Dict[str, CodeSummary] = {}
        self.dependency_map: Dict[str, Set[str]] = defaultdict(set)
        self.reverse_dependency_map: Dict[str, Set[str]] = defaultdict(set)
    
    def add_structure(self, structure: CodeStructure) -> None:
        """Add a code structure to the dependency graph"""
        node = DependencyNode(
            name=structure.name,
            type=structure.type,
            file_path=structure.file_path,
            dependencies=structure.dependencies,
            dependents=[],
            content=structure.content,
            metadata={
                'modifiers': structure.modifiers or [],
                'return_type': structure.return_type,
                'parameters': structure.parameters or [],
                'parent_class': structure.parent_class,
                'start_line': structure.start_line,
                'end_line': structure.end_line
            }
        )
        
        self.nodes[structure.name] = node
        
        # Build dependency maps
        for dep in structure.dependencies:
            self.dependency_map[structure.name].add(dep)
            self.reverse_dependency_map[dep].add(structure.name)
    
    def build_graph(self, structures: List[CodeStructure]) -> None:
        """Build the complete dependency graph from structures"""
        print("Building dependency graph...")
        
        # Add all structures
        for structure in structures:
            self.add_structure(structure)
        
        # Update dependents
        for node_name, node in self.nodes.items():
            for dep in node.dependencies:
                if dep in self.nodes:
                    self.nodes[dep].dependents.append(node_name)
        
        print(f"Built dependency graph with {len(self.nodes)} nodes")
        self._analyze_graph()
    
    def _analyze_graph(self) -> None:
        """Analyze the dependency graph for insights"""
        # Find root nodes (no dependencies)
        root_nodes = [name for name, node in self.nodes.items() if not node.dependencies]
        print(f"Found {len(root_nodes)} root nodes: {root_nodes}")
        
        # Find leaf nodes (no dependents)
        leaf_nodes = [name for name, node in self.nodes.items() if not node.dependents]
        print(f"Found {len(leaf_nodes)} leaf nodes: {leaf_nodes}")
        
        # Find circular dependencies
        circular_deps = self._find_circular_dependencies()
        if circular_deps:
            print(f"Found {len(circular_deps)} circular dependencies")
            for cycle in circular_deps[:3]:  # Show first 3
                print(f"  Cycle: {' -> '.join(cycle)}")
    
    def _find_circular_dependencies(self) -> List[List[str]]:
        """Find circular dependencies using DFS"""
        visited = set()
        rec_stack = set()
        cycles = []
        
        def dfs(node: str, path: List[str]) -> None:
            if node in rec_stack:
                # Found a cycle
                cycle_start = path.index(node)
                cycle = path[cycle_start:] + [node]
                cycles.append(cycle)
                return
            
            if node in visited:
                return
            
            visited.add(node)
            rec_stack.add(node)
            path.append(node)
            
            for dep in self.dependency_map.get(node, []):
                if dep in self.nodes:  # Only check nodes we have
                    dfs(dep, path)
            
            path.pop()
            rec_stack.remove(node)
        
        for node_name in self.nodes:
            if node_name not in visited:
                dfs(node_name, [])
        
        return cycles
    
    def get_neighborhood(self, node_name: str, depth: int = 1) -> List[str]:
        """Get the neighborhood of a node (dependencies and dependents up to specified depth)"""
        if node_name not in self.nodes:
            return []
        
        neighborhood = set()
        queue = deque([(node_name, 0)])  # (node, depth)
        visited = {node_name}
        
        while queue:
            current, current_depth = queue.popleft()
            neighborhood.add(current)
            
            if current_depth >= depth:
                continue
            
            # Add dependencies
            for dep in self.dependency_map.get(current, []):
                if dep not in visited and dep in self.nodes:
                    visited.add(dep)
                    queue.append((dep, current_depth + 1))
            
            # Add dependents
            for dep in self.reverse_dependency_map.get(current, []):
                if dep not in visited and dep in self.nodes:
                    visited.add(dep)
                    queue.append((dep, current_depth + 1))
        
        return list(neighborhood)
    
    def get_dependency_chain(self, node_name: str) -> List[str]:
        """Get the dependency chain for a node (all dependencies in order)"""
        if node_name not in self.nodes:
            return []
        
        # Topological sort
        in_degree = defaultdict(int)
        for node in self.nodes.values():
            for dep in node.dependencies:
                if dep in self.nodes:
                    in_degree[dep] += 1
        
        queue = deque([node for node in self.nodes if in_degree[node] == 0])
        result = []
        
        while queue:
            current = queue.popleft()
            result.append(current)
            
            for dep in self.dependency_map.get(current, []):
                if dep in self.nodes:
                    in_degree[dep] -= 1
                    if in_degree[dep] == 0:
                        queue.append(dep)
        
        return result
    
    def add_summary(self, summary: CodeSummary) -> None:
        """Add a structured summary for a code element"""
        self.summaries[summary.name] = summary
    
    def get_context_for_migration(self, target_node: str, include_depth: int = 2) -> Dict[str, Any]:
        """Get comprehensive context for migrating a specific node"""
        if target_node not in self.nodes:
            return {}
        
        # Get the target node
        target = self.nodes[target_node]
        
        # Get neighborhood
        neighborhood = self.get_neighborhood(target_node, include_depth)
        
        # Get dependency chain
        dependency_chain = self.get_dependency_chain(target_node)
        
        # Build context
        context = {
            'target_node': {
                'name': target.name,
                'type': target.type,
                'file_path': target.file_path,
                'content': target.content,
                'metadata': target.metadata,
                'summary': self.summaries.get(target.name)
            },
            'dependencies': [],
            'dependents': [],
            'neighborhood': [],
            'dependency_chain': dependency_chain
        }
        
        # Add dependency details
        for dep_name in target.dependencies:
            if dep_name in self.nodes:
                dep_node = self.nodes[dep_name]
                context['dependencies'].append({
                    'name': dep_name,
                    'type': dep_node.type,
                    'file_path': dep_node.file_path,
                    'content': dep_node.content,
                    'summary': self.summaries.get(dep_name)
                })
        
        # Add dependent details
        for dep_name in target.dependents:
            if dep_name in self.nodes:
                dep_node = self.nodes[dep_name]
                context['dependents'].append({
                    'name': dep_name,
                    'type': dep_node.type,
                    'file_path': dep_node.file_path,
                    'content': dep_node.content,
                    'summary': self.summaries.get(dep_name)
                })
        
        # Add neighborhood details
        for node_name in neighborhood:
            if node_name != target_node and node_name in self.nodes:
                node = self.nodes[node_name]
                context['neighborhood'].append({
                    'name': node_name,
                    'type': node.type,
                    'file_path': node.file_path,
                    'content': node.content,
                    'summary': self.summaries.get(node_name)
                })
        
        return context
    
    def export_knowledge_base(self, output_path: str) -> None:
        """Export the knowledge base to JSON"""
        knowledge_base = {
            'nodes': {name: asdict(node) for name, node in self.nodes.items()},
            'summaries': {name: asdict(summary) for name, summary in self.summaries.items()},
            'dependency_map': {name: list(deps) for name, deps in self.dependency_map.items()},
            'reverse_dependency_map': {name: list(deps) for name, deps in self.reverse_dependency_map.items()}
        }
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(knowledge_base, f, indent=2, default=str)
        
        print(f"Exported knowledge base to {output_path}")
    
    def import_knowledge_base(self, input_path: str) -> None:
        """Import knowledge base from JSON"""
        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Reconstruct nodes
        for name, node_data in data['nodes'].items():
            self.nodes[name] = DependencyNode(**node_data)
        
        # Reconstruct summaries
        for name, summary_data in data['summaries'].items():
            self.summaries[name] = CodeSummary(**summary_data)
        
        # Reconstruct dependency maps
        for name, deps in data['dependency_map'].items():
            self.dependency_map[name] = set(deps)
        
        for name, deps in data['reverse_dependency_map'].items():
            self.reverse_dependency_map[name] = set(deps)
        
        print(f"Imported knowledge base from {input_path}")
    
    def get_migration_order(self) -> List[str]:
        """Get the optimal order for migrating components (dependency-first)"""
        # Use topological sort to get dependency order
        return self.get_dependency_chain(list(self.nodes.keys())[0]) if self.nodes else []
    
    def get_complexity_metrics(self) -> Dict[str, Any]:
        """Calculate complexity metrics for the codebase"""
        metrics = {
            'total_nodes': len(self.nodes),
            'node_types': defaultdict(int),
            'avg_dependencies': 0,
            'max_dependencies': 0,
            'circular_dependencies': len(self._find_circular_dependencies()),
            'root_nodes': len([n for n in self.nodes.values() if not n.dependencies]),
            'leaf_nodes': len([n for n in self.nodes.values() if not n.dependents])
        }
        
        total_deps = 0
        for node in self.nodes.values():
            metrics['node_types'][node.type] += 1
            total_deps += len(node.dependencies)
            metrics['max_dependencies'] = max(metrics['max_dependencies'], len(node.dependencies))
        
        if self.nodes:
            metrics['avg_dependencies'] = total_deps / len(self.nodes)
        
        return dict(metrics)
