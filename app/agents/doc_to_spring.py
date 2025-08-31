import json
import os
from typing import List, Dict, Any
from app.clients.azure_openai_client import AzureLLMClient
from app.agents.prompts import DOC_TO_SPRING_PROMPT
from app.utils.json_utils import safe_json_list


class DocToSpringAgent:
    def __init__(self):
        self.client = AzureLLMClient()
        self.knowledge_base = None

    def _load_knowledge_base(self, knowledge_base_path: str = "data/workspace/knowledge_base.json") -> Dict[str, Any]:
        """Load the knowledge base from JSON file"""
        try:
            if os.path.exists(knowledge_base_path):
                with open(knowledge_base_path, 'r', encoding='utf-8') as f:
                    self.knowledge_base = json.load(f)
                print(f"Successfully loaded knowledge base with {len(self.knowledge_base.get('nodes', {}))} components")
                return self.knowledge_base
            else:
                print(f"Knowledge base not found at {knowledge_base_path}")
                return {}
        except Exception as e:
            print(f"Error loading knowledge base: {e}")
            return {}

    def _extract_component_details_from_kb(self) -> str:
        """Extract detailed component information from knowledge base"""
        if not self.knowledge_base or 'nodes' not in self.knowledge_base:
            return "No knowledge base available for component analysis."
        
        nodes = self.knowledge_base['nodes']
        component_details = []
        
        # Group components by type
        components_by_type = {}
        for name, node in nodes.items():
            comp_type = node.get('type', 'unknown')
            if comp_type not in components_by_type:
                components_by_type[comp_type] = []
            components_by_type[comp_type].append((name, node))
        
        # Generate detailed analysis for each component type
        for comp_type, components in components_by_type.items():
            component_details.append(f"\n### {comp_type.title()} Components ({len(components)}):")
            
            for name, node in components:
                dependencies = node.get('dependencies', [])
                dependents = node.get('dependents', [])
                content = node.get('content', '')
                
                # Extract key information from content
                content_preview = content[:500] + "..." if len(content) > 500 else content
                
                component_details.append(f"""
**Component: {name}**
- **File**: {node.get('file_path', 'Unknown')}
- **Dependencies**: {', '.join(dependencies[:5])}{'...' if len(dependencies) > 5 else ''}
- **Dependents**: {', '.join(dependents[:5])}{'...' if len(dependents) > 5 else ''}
- **Content Preview**: 
```java
{content_preview}
```
""")
        
        return "\n".join(component_details)

    def _extract_dependency_analysis_from_kb(self) -> str:
        """Extract dependency analysis from knowledge base"""
        if not self.knowledge_base or 'dependency_map' not in self.knowledge_base:
            return "No dependency information available."
        
        dependency_map = self.knowledge_base.get('dependency_map', {})
        reverse_dependency_map = self.knowledge_base.get('reverse_dependency_map', {})
        
        # Find core components (those with many dependents)
        core_components = []
        for name, dependents in reverse_dependency_map.items():
            if len(dependents) >= 3:  # Components used by 3+ other components
                core_components.append((name, len(dependents)))
        
        # Sort by number of dependents
        core_components.sort(key=lambda x: x[1], reverse=True)
        
        # Find leaf components (those with no dependents)
        leaf_components = [name for name, deps in dependency_map.items() if not deps]
        
        dependency_analysis = f"""
### Dependency Analysis:
- **Total Components**: {len(dependency_map)}
- **Core Components** (highly used): {', '.join([f"{name}({count})" for name, count in core_components[:10]])}
- **Leaf Components** (no dependencies): {', '.join(leaf_components[:10])}

### Critical Dependencies for Spring Boot Migration:
"""
        
        # Add detailed dependency chains for core components
        for name, count in core_components[:5]:
            deps = dependency_map.get(name, [])
            dependents = reverse_dependency_map.get(name, [])
            
            dependency_analysis += f"""
**{name}** (used by {count} components):
- **Dependencies**: {', '.join(deps[:5])}
- **Dependents**: {', '.join(dependents[:5])}
- **Migration Priority**: HIGH (core component)
"""
        
        return dependency_analysis

    def _extract_business_logic_from_kb(self) -> str:
        """Extract business logic patterns from knowledge base"""
        if not self.knowledge_base or 'nodes' not in self.knowledge_base:
            return "No business logic information available."
        
        nodes = self.knowledge_base['nodes']
        business_logic_patterns = []
        
        # Look for service-like components
        service_components = []
        for name, node in nodes.items():
            content = node.get('content', '').lower()
            if 'service' in name.lower() or 'service' in content:
                service_components.append((name, node))
        
        business_logic_analysis = f"""
### Business Logic Analysis:
- **Service Components Found**: {len(service_components)}

### Key Business Services:
"""
        
        for name, node in service_components[:10]:
            content = node.get('content', '')
            # Extract method signatures and business logic
            lines = content.split('\n')
            methods = [line.strip() for line in lines if 'public' in line and '(' in line and ')' in line]
            
            business_logic_analysis += f"""
**{name}**:
- **Methods**: {len(methods)}
- **Key Methods**: {', '.join(methods[:3])}
- **Content Preview**: 
```java
{content[:300]}...
```
"""
        
        return business_logic_analysis

    def run(self, migration_doc: str, context_snippets: List[str], knowledge_base_path: str = "data/workspace/knowledge_base.json") -> List[Dict[str, str]]:
        """Generate comprehensive Spring Boot code from migration documentation with knowledge base context"""
        print("Running DocToSpringAgent with knowledge base integration...")
        
        # Load knowledge base
        self._load_knowledge_base(knowledge_base_path)
        
        # Extract detailed context from knowledge base
        component_details = self._extract_component_details_from_kb()
        dependency_analysis = self._extract_dependency_analysis_from_kb()
        business_logic_analysis = self._extract_business_logic_from_kb()
        
        # Prepare comprehensive context
        context_summary = self._analyze_context_snippets(context_snippets)
        
        # Create detailed prompt with enhanced context including knowledge base
        enhanced_prompt = f"""
{migration_doc}

## Legacy Code Context Analysis:
{context_summary}

## Knowledge Base Component Analysis:
{component_details}

## Dependency Analysis:
{dependency_analysis}

## Business Logic Analysis:
{business_logic_analysis}

## Additional Context from Legacy Code:
"""
        
        # Add key code snippets for context
        for i, snippet in enumerate(context_snippets[:15]):  # Limit to first 15 snippets
            enhanced_prompt += f"\n### Code Snippet {i+1}:\n```java\n{snippet[:1000]}\n```\n"
        
        enhanced_prompt += """

## Spring Boot Generation Instructions:
Based on the comprehensive analysis above, generate COMPREHENSIVE Spring Boot code that:
1. **Preserves ALL business logic** from the original components
2. **Maintains dependency relationships** as Spring beans
3. **Implements proper layering** (Controller -> Service -> Repository)
4. **Includes all necessary annotations** (@Service, @Repository, @Controller, @Entity, etc.)
5. **Handles all detected dependencies** and relationships
6. **Implements proper error handling** and validation
7. **Uses Spring Security** for authentication/authorization if needed
8. **Includes proper configuration** for database, security, etc.

Generate COMPREHENSIVE Spring Boot code that fully implements ALL the business logic shown above.
"""
        
        print(f"Received migration_doc (truncated to 6000 chars): {migration_doc[:6000]}")
        print(f"Received context_snippets (first 10): {len(context_snippets)}")
        print(f"Knowledge base components: {len(self.knowledge_base.get('nodes', {})) if self.knowledge_base else 0}")
        
        messages = [
            {"role": "system", "content": DOC_TO_SPRING_PROMPT},
            {"role": "user", "content": enhanced_prompt}
        ]
        
        response = self.client.chat(messages)
        print(f"Raw response from AzureLLMClient: {response[:1000]}")
        
        # Parse the response
        try:
            spring_files = safe_json_list(response)
            print(f"Successfully parsed {len(spring_files)} Spring Boot files")
            return spring_files
        except Exception as e:
            print(f"Error parsing response: {e}")
            # Return a basic Spring Boot structure as fallback
            return self._create_fallback_spring_structure()
    
    def _analyze_context_snippets(self, context_snippets: List[str]) -> str:
        """Analyze context snippets to provide better guidance"""
        if not context_snippets:
            return "No legacy code context available."
        
        # Analyze the snippets for patterns
        total_snippets = len(context_snippets)
        total_chars = sum(len(snippet) for snippet in context_snippets)
        
        # Look for common patterns
        patterns = {
            "controllers": sum(1 for s in context_snippets if "@Controller" in s or "extends" in s and "Controller" in s),
            "services": sum(1 for s in context_snippets if "@Service" in s or "Service" in s),
            "entities": sum(1 for s in context_snippets if "@Entity" in s or "class" in s and "{" in s),
            "repositories": sum(1 for s in context_snippets if "Repository" in s or "DAO" in s),
            "utilities": sum(1 for s in context_snippets if "util" in s.lower() or "helper" in s.lower()),
            "configurations": sum(1 for s in context_snippets if "@Configuration" in s or "config" in s.lower())
        }
        
        analysis = f"""
### Legacy Code Analysis:
- **Total Snippets**: {total_snippets}
- **Total Code Size**: {total_chars:,} characters
- **Average Snippet Size**: {total_chars // total_snippets if total_snippets > 0 else 0} characters

### Detected Patterns:
- **Controllers/Web Layer**: {patterns['controllers']} components
- **Services/Business Logic**: {patterns['services']} components  
- **Entities/Data Models**: {patterns['entities']} components
- **Repositories/Data Access**: {patterns['repositories']} components
- **Utilities/Helpers**: {patterns['utilities']} components
- **Configurations**: {patterns['configurations']} components

### Migration Requirements:
Based on the analysis, ensure the Spring Boot implementation includes:
1. **Complete REST Controllers** for all web functionality
2. **Full Service Layer** with all business logic
3. **Complete Entity Models** with proper JPA annotations
4. **Repository Layer** with custom queries if needed
5. **Configuration Classes** for security, database, etc.
6. **Utility Classes** for helper functions
7. **DTOs** for request/response handling
8. **Exception Handling** and validation
"""
        
        return analysis
    
    def _create_fallback_spring_structure(self) -> List[Dict[str, str]]:
        """Create a basic Spring Boot structure as fallback"""
        return [
            {
                "path": "pom.xml",
                "content": """<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 https://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>
    <parent>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-parent</artifactId>
        <version>3.1.0</version>
        <relativePath/>
    </parent>
    <groupId>com.example</groupId>
    <artifactId>spring-project</artifactId>
    <version>0.0.1-SNAPSHOT</version>
    <name>Spring Project</name>
    <description>Spring Boot application</description>
    <properties>
        <java.version>17</java.version>
    </properties>
    <dependencies>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-web</artifactId>
        </dependency>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-data-jpa</artifactId>
        </dependency>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-validation</artifactId>
        </dependency>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-test</artifactId>
            <scope>test</scope>
        </dependency>
        <dependency>
            <groupId>com.h2database</groupId>
            <artifactId>h2</artifactId>
            <scope>runtime</scope>
        </dependency>
    </dependencies>
    <build>
        <plugins>
            <plugin>
                <groupId>org.springframework.boot</groupId>
                <artifactId>spring-boot-maven-plugin</artifactId>
            </plugin>
        </plugins>
    </build>
</project>"""
            },
            {
                "path": "src/main/resources/application.yml",
                "content": """spring:
  datasource:
    url: jdbc:h2:mem:testdb
    driver-class-name: org.h2.Driver
    username: sa
    password: password
  jpa:
    hibernate:
      ddl-auto: update
    show-sql: true
logging:
  level:
    root: INFO
    org.springframework: DEBUG
server:
  port: 8080"""
            },
            {
                "path": "src/main/java/com/example/Application.java",
                "content": """package com.example;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@SpringBootApplication
public class Application {

    public static void main(String[] args) {
        SpringApplication.run(Application.class, args);
    }
}"""
            }
        ]
