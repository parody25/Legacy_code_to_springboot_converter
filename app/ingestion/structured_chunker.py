import os
import re
from typing import List, Dict, Any, Tuple, Optional
import javalang
from dataclasses import dataclass


@dataclass
class CodeStructure:
    """Represents a structured code element with metadata"""
    type: str  # 'class', 'interface', 'method', 'enum', 'annotation', 'constant'
    name: str
    content: str
    file_path: str
    start_line: int
    end_line: int
    dependencies: List[str]  # List of class/method dependencies
    parent_class: Optional[str] = None
    modifiers: List[str] = None
    return_type: Optional[str] = None
    parameters: List[Dict[str, str]] = None  # [{"type": "String", "name": "param1"}]


class StructuredChunker:
    """Chunks Java code by structural elements instead of random line splitting"""
    
    def __init__(self):
        self.structures: List[CodeStructure] = []
    
    def chunk_file(self, file_path: str, content: str) -> List[CodeStructure]:
        """Parse a Java file and extract structured chunks"""
        if not file_path.endswith('.java'):
            return []
        
        print(f"Parsing file: {file_path}")
        
        try:
            # Parse with javalang
            tree = javalang.parse.parse(content)
            
            # Extract package and imports for context
            package_name = self._extract_package(content)
            imports = self._extract_imports(content)
            
            # Extract different structural elements
            structures = []
            
            # Extract classes
            for path, node in tree:
                if isinstance(node, javalang.tree.ClassDeclaration):
                    class_struct = self._extract_class_structure(node, file_path, content, package_name, imports)
                    structures.append(class_struct)
                    
                    # Extract methods within this class
                    for method_path, method_node in tree:
                        if (isinstance(method_node, javalang.tree.MethodDeclaration) and 
                            method_path[0] == node):
                            method_struct = self._extract_method_structure(
                                method_node, file_path, content, class_struct.name, package_name, imports
                            )
                            structures.append(method_struct)
            
            # Extract interfaces
            for path, node in tree:
                if isinstance(node, javalang.tree.InterfaceDeclaration):
                    interface_struct = self._extract_interface_structure(node, file_path, content, package_name, imports)
                    structures.append(interface_struct)
            
            # Extract enums
            for path, node in tree:
                if isinstance(node, javalang.tree.EnumDeclaration):
                    enum_struct = self._extract_enum_structure(node, file_path, content, package_name, imports)
                    structures.append(enum_struct)
            
            # Extract annotations
            for path, node in tree:
                if isinstance(node, javalang.tree.AnnotationDeclaration):
                    annotation_struct = self._extract_annotation_structure(node, file_path, content, package_name, imports)
                    structures.append(annotation_struct)
            
            # Extract constants and fields outside classes
            constants = self._extract_constants(content, file_path, package_name)
            structures.extend(constants)
            
            return structures
            
        except Exception as e:
            print(f"Error parsing {file_path}: {e}")
            # Fallback to regex-based extraction
            return self._fallback_chunking(file_path, content)
    
    def _extract_package(self, content: str) -> str:
        """Extract package declaration"""
        match = re.search(r'package\s+([\w.]+);', content)
        return match.group(1) if match else ""
    
    def _extract_imports(self, content: str) -> List[str]:
        """Extract import statements"""
        imports = re.findall(r'import\s+([\w.*]+);', content)
        return imports
    
    def _extract_class_structure(self, node, file_path: str, content: str, package: str, imports: List[str]) -> CodeStructure:
        """Extract class structure with dependencies"""
        class_name = node.name
        start_line = node.position.line if node.position else 1
        
        # Find class content boundaries
        class_content = self._extract_node_content(content, node)
        
        # Extract dependencies
        dependencies = self._extract_dependencies(class_content, imports)
        
        # Extract modifiers
        modifiers = [mod.value for mod in node.modifiers] if node.modifiers else []
        
        return CodeStructure(
            type='class',
            name=class_name,
            content=class_content,
            file_path=file_path,
            start_line=start_line,
            end_line=start_line + class_content.count('\n'),
            dependencies=dependencies,
            modifiers=modifiers
        )
    
    def _extract_method_structure(self, node, file_path: str, content: str, parent_class: str, package: str, imports: List[str]) -> CodeStructure:
        """Extract method structure with dependencies"""
        method_name = node.name
        start_line = node.position.line if node.position else 1
        
        # Find method content
        method_content = self._extract_node_content(content, node)
        
        # Extract dependencies
        dependencies = self._extract_dependencies(method_content, imports)
        
        # Extract parameters
        parameters = []
        if node.parameters:
            for param in node.parameters:
                param_type = param.type.name if param.type else "Object"
                parameters.append({"type": param_type, "name": param.name})
        
        # Extract return type
        return_type = node.return_type.name if node.return_type else "void"
        
        # Extract modifiers
        modifiers = [mod.value for mod in node.modifiers] if node.modifiers else []
        
        return CodeStructure(
            type='method',
            name=method_name,
            content=method_content,
            file_path=file_path,
            start_line=start_line,
            end_line=start_line + method_content.count('\n'),
            dependencies=dependencies,
            parent_class=parent_class,
            modifiers=modifiers,
            return_type=return_type,
            parameters=parameters
        )
    
    def _extract_interface_structure(self, node, file_path: str, content: str, package: str, imports: List[str]) -> CodeStructure:
        """Extract interface structure"""
        interface_name = node.name
        start_line = node.position.line if node.position else 1
        interface_content = self._extract_node_content(content, node)
        dependencies = self._extract_dependencies(interface_content, imports)
        modifiers = [mod.value for mod in node.modifiers] if node.modifiers else []
        
        return CodeStructure(
            type='interface',
            name=interface_name,
            content=interface_content,
            file_path=file_path,
            start_line=start_line,
            end_line=start_line + interface_content.count('\n'),
            dependencies=dependencies,
            modifiers=modifiers
        )
    
    def _extract_enum_structure(self, node, file_path: str, content: str, package: str, imports: List[str]) -> CodeStructure:
        """Extract enum structure"""
        enum_name = node.name
        start_line = node.position.line if node.position else 1
        enum_content = self._extract_node_content(content, node)
        dependencies = self._extract_dependencies(enum_content, imports)
        modifiers = [mod.value for mod in node.modifiers] if node.modifiers else []
        
        return CodeStructure(
            type='enum',
            name=enum_name,
            content=enum_content,
            file_path=file_path,
            start_line=start_line,
            end_line=start_line + enum_content.count('\n'),
            dependencies=dependencies,
            modifiers=modifiers
        )
    
    def _extract_annotation_structure(self, node, file_path: str, content: str, package: str, imports: List[str]) -> CodeStructure:
        """Extract annotation structure"""
        annotation_name = node.name
        start_line = node.position.line if node.position else 1
        annotation_content = self._extract_node_content(content, node)
        dependencies = self._extract_dependencies(annotation_content, imports)
        modifiers = [mod.value for mod in node.modifiers] if node.modifiers else []
        
        return CodeStructure(
            type='annotation',
            name=annotation_name,
            content=annotation_content,
            file_path=file_path,
            start_line=start_line,
            end_line=start_line + annotation_content.count('\n'),
            dependencies=dependencies,
            modifiers=modifiers
        )
    
    def _extract_constants(self, content: str, file_path: str, package: str) -> List[CodeStructure]:
        """Extract constants and fields outside classes"""
        constants = []
        
        # Find public static final fields (constants)
        constant_pattern = r'public\s+static\s+final\s+(\w+)\s+(\w+)\s*=\s*([^;]+);'
        matches = re.finditer(constant_pattern, content)
        
        for match in matches:
            const_type = match.group(1)
            const_name = match.group(2)
            const_value = match.group(3)
            
            # Find the line number
            lines = content[:match.start()].split('\n')
            start_line = len(lines)
            
            constant_content = f"public static final {const_type} {const_name} = {const_value};"
            
            constants.append(CodeStructure(
                type='constant',
                name=const_name,
                content=constant_content,
                file_path=file_path,
                start_line=start_line,
                end_line=start_line,
                dependencies=[],
                modifiers=['public', 'static', 'final']
            ))
        
        return constants
    
    def _extract_node_content(self, content: str, node) -> str:
        """Extract the actual content of a node from the source."""
        if not node.position:
            return str(node)

        lines = content.split('\n')
        start_line = node.position.line - 1  # Convert to 0-based index

        # Use the node's children to determine the end position if available
        end_line = start_line + 1
        if hasattr(node, 'children') and node.children:
            # Find the maximum line number among the node's children
            child_positions = [
                child.position.line for child in node.children if hasattr(child, 'position') and child.position
            ]
            if child_positions:
                end_line = max(child_positions)

        # If children are not available, fall back to brace matching
        if end_line == start_line + 1:
            brace_count = 0
            in_node = False
            for i in range(start_line, len(lines)):
                line = lines[i]
                if '{' in line:
                    brace_count += line.count('{')
                    in_node = True
                if '}' in line:
                    brace_count -= line.count('}')
                    if in_node and brace_count == 0:
                        end_line = i + 1
                        break

        # Extract the content between start_line and end_line
        return '\n'.join(lines[start_line:end_line])
    
    def _extract_dependencies(self, content: str, imports: List[str]) -> List[str]:
        """Extract dependencies from content"""
        dependencies = []
        
        # Look for class instantiations, method calls, etc.
        # This is a simplified approach - you'd want more sophisticated analysis
        class_pattern = r'new\s+(\w+)'
        method_pattern = r'(\w+)\.(\w+)\('
        
        # Find class instantiations
        class_matches = re.findall(class_pattern, content)
        dependencies.extend(class_matches)
        
        # Find method calls (simplified)
        method_matches = re.findall(method_pattern, content)
        dependencies.extend([match[0] for match in method_matches])
        
        # Add imports as potential dependencies
        for imp in imports:
            if not imp.endswith('.*'):
                class_name = imp.split('.')[-1]
                dependencies.append(class_name)
        
        return list(set(dependencies))  # Remove duplicates
    
    def _fallback_chunking(self, file_path: str, content: str) -> List[CodeStructure]:
        """Fallback chunking using regex patterns when javalang fails"""
        structures = []
        
        # Extract classes using regex
        class_pattern = r'(public\s+)?class\s+(\w+)(?:\s+extends\s+\w+)?(?:\s+implements\s+[\w\s,]+)?\s*\{'
        class_matches = re.finditer(class_pattern, content)
        
        for match in class_matches:
            class_name = match.group(2)
            start_line = content[:match.start()].count('\n') + 1
            
            # Find class end (simplified)
            brace_count = 0
            end_pos = match.end()
            for i in range(match.end(), len(content)):
                if content[i] == '{':
                    brace_count += 1
                elif content[i] == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        end_pos = i + 1
                        break
            
            class_content = content[match.start():end_pos]
            end_line = start_line + class_content.count('\n')
            
            structures.append(CodeStructure(
                type='class',
                name=class_name,
                content=class_content,
                file_path=file_path,
                start_line=start_line,
                end_line=end_line,
                dependencies=self._extract_dependencies(class_content, [])
            ))
        
        return structures
    
    def chunk_project(self, project_dir: str) -> List[CodeStructure]:
        """Chunk an entire project using structured approach"""
        all_structures = []
        
        for root, dirs, files in os.walk(project_dir):
            for file in files:
                if file.endswith('.java'):
                    file_path = os.path.join(root, file)
                    relative_path = os.path.relpath(file_path, project_dir)
                    
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        structures = self.chunk_file(relative_path, content)
                        all_structures.extend(structures)
                        
                    except Exception as e:
                        print(f"Error processing {file_path}: {e}")
        
        print(f"Extracted {len(all_structures)} structural elements")
        return all_structures
