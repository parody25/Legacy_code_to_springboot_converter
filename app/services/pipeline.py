import json
import os
import shutil
import tempfile
from typing import Dict, Any, List
import xml.etree.ElementTree as ET

from app.agents.code_to_doc import CodeToDocumentAgent
from app.agents.doc_to_spring import DocToSpringAgent
from app.agents.evaluator import EvaluatorAgent
from app.agents.junit_generator import JUnitGeneratorAgent
from app.config import settings
from app.ingestion.ingest import chunk_project


class ConversionPipeline:
    def __init__(self) -> None:
        self.code_to_doc = CodeToDocumentAgent()
        self.evaluator = EvaluatorAgent()
        self.doc_to_spring = DocToSpringAgent()
        self.junit_gen = JUnitGeneratorAgent()

    def _write_files(self, base_dir: str, files: List[Dict[str, str]]) -> None:
        for f in files:
            target = os.path.join(base_dir, f["path"].lstrip("/"))
            os.makedirs(os.path.dirname(target), exist_ok=True)
            with open(target, "w", encoding="utf-8") as out:
                out.write(f["content"])

    def _ensure_pom_dependencies(self, project_dir: str) -> None:
        """Ensure pom.xml has all necessary Spring Boot dependencies"""
        pom_path = os.path.join(project_dir, "pom.xml")
        if not os.path.exists(pom_path):
            print("No pom.xml found, skipping dependency check")
            return
        
        print("Checking and fixing pom.xml dependencies...")
        
        try:
            # Parse existing pom.xml
            tree = ET.parse(pom_path)
            root = tree.getroot()
            
            # Define namespace
            ns = {'mvn': 'http://maven.apache.org/POM/4.0.0'}
            
            # Find dependencies section
            dependencies = root.find('.//mvn:dependencies', ns)
            if dependencies is None:
                # Create dependencies section if it doesn't exist
                project = root.find('.//mvn:project', ns)
                if project is not None:
                    dependencies = ET.SubElement(project, 'dependencies')
            
            # Required dependencies to check/add
            required_deps = [
                {
                    'groupId': 'org.springframework.boot',
                    'artifactId': 'spring-boot-starter-web',
                    'description': 'Web starter for @RestController, @RequestMapping, etc.'
                },
                {
                    'groupId': 'org.springframework.boot',
                    'artifactId': 'spring-boot-starter',
                    'description': 'Core Spring Boot starter'
                },
                {
                    'groupId': 'org.springframework.boot',
                    'artifactId': 'spring-boot-starter-test',
                    'scope': 'test',
                    'description': 'Testing starter'
                }
            ]
            
            # Check for existing dependencies
            existing_deps = set()
            for dep in dependencies.findall('.//mvn:dependency', ns):
                group_id = dep.find('mvn:groupId', ns)
                artifact_id = dep.find('mvn:artifactId', ns)
                if group_id is not None and artifact_id is not None:
                    existing_deps.add(f"{group_id.text}:{artifact_id.text}")
            
            # Add missing dependencies
            added_deps = []
            for req_dep in required_deps:
                dep_key = f"{req_dep['groupId']}:{req_dep['artifactId']}"
                if dep_key not in existing_deps:
                    print(f"Adding missing dependency: {dep_key}")
                    
                    dependency = ET.SubElement(dependencies, 'dependency')
                    
                    group_id = ET.SubElement(dependency, 'groupId')
                    group_id.text = req_dep['groupId']
                    
                    artifact_id = ET.SubElement(dependency, 'artifactId')
                    artifact_id.text = req_dep['artifactId']
                    
                    if 'scope' in req_dep:
                        scope = ET.SubElement(dependency, 'scope')
                        scope.text = req_dep['scope']
                    
                    added_deps.append(dep_key)
            
            if added_deps:
                print(f"Added dependencies: {', '.join(added_deps)}")
                # Write back the updated pom.xml
                tree.write(pom_path, encoding='utf-8', xml_declaration=True)
            else:
                print("All required dependencies already present")
                
        except Exception as e:
            print(f"Error fixing pom.xml dependencies: {e}")
            # Create a basic pom.xml with required dependencies
            self._create_basic_pom(pom_path)

    def _create_basic_pom(self, pom_path: str) -> None:
        """Create a basic pom.xml with essential Spring Boot dependencies"""
        basic_pom = '''<?xml version="1.0" encoding="UTF-8"?>
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
            <artifactId>spring-boot-starter</artifactId>
        </dependency>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-test</artifactId>
            <scope>test</scope>
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
</project>'''
        
        with open(pom_path, 'w', encoding='utf-8') as f:
            f.write(basic_pom)
        print(f"Created basic pom.xml with essential dependencies")

    def run(self, project_dir: str, output_dir: str) -> Dict[str, Any]:
        # Step 1: Chunk the legacy code
        chunks = chunk_project(project_dir)

        # Step 2: Generate migration documentation
        migration_doc = self.code_to_doc.run(chunks)

        # Step 3: Evaluate documentation quality against legacy code
        evaluation = self.evaluator.run(migration_doc, chunks, project_dir)

        # Step 4: Generate Spring Boot code based on evaluated documentation
        context_snippets = [c[2] for c in chunks[:20]]
        spring_files = self.doc_to_spring.run(migration_doc, context_snippets)

        # Step 5: Generate project structure and write files
        temp_dir = tempfile.mkdtemp(prefix="springgen-")
        self._write_files(temp_dir, spring_files)

        # Step 6: Ensure pom.xml has all necessary dependencies
        self._ensure_pom_dependencies(temp_dir)

        # Step 7: Generate JUnit tests
        test_files = self.junit_gen.run(spring_files)
        self._write_files(temp_dir, test_files)

        # Step 8: Save outputs
        os.makedirs(output_dir, exist_ok=True)
        with open(os.path.join(output_dir, "migration_doc.md"), "w", encoding="utf-8") as f:
            f.write(migration_doc)
        with open(os.path.join(output_dir, "evaluation.json"), "w", encoding="utf-8") as f:
            json.dump(evaluation, f, indent=2)

        # Step 9: Copy final project
        final_project_dir = os.path.join(output_dir, "spring_project")
        if os.path.exists(final_project_dir):
            shutil.rmtree(final_project_dir)
        shutil.copytree(temp_dir, final_project_dir)

        return {
            "migration_doc": migration_doc,
            "evaluation": evaluation,
            "spring_files": spring_files,
            "test_files": test_files,
            "project_dir": final_project_dir,
        }

