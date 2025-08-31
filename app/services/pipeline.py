import json
import os
import shutil
import tempfile
from typing import Dict, Any, List
import xml.etree.ElementTree as ET

from app.ingestion.structured_chunker import StructuredChunker
from app.agents.enhanced_code_to_doc import EnhancedCodeToDocumentAgent
from app.agents.doc_to_spring import DocToSpringAgent
from app.agents.evaluator import EvaluatorAgent
from app.agents.junit_generator import JUnitGeneratorAgent
from app.config import settings


class ConversionPipeline:
    def __init__(self) -> None:
        self.structured_chunker = StructuredChunker()
        self.enhanced_code_to_doc = EnhancedCodeToDocumentAgent()
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
            print("No pom.xml found, creating comprehensive one...")
            self._create_basic_pom(pom_path)
            return
        
        print("Checking pom.xml for required dependencies...")
        
        try:
            # Read the pom.xml content
            with open(pom_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check if required dependencies are present
            required_deps = [
                'spring-boot-starter-web',
                'spring-boot-starter-data-jpa',
                'spring-boot-starter-security',
                'spring-boot-starter-validation',
                'spring-boot-starter-actuator',
                'spring-boot-starter-cache',
                'spring-boot-starter-mail',
                'spring-boot-starter-test',
                'h2',
                'jakarta.persistence-api',
                'jakarta.validation-api'
            ]
            
            missing_deps = []
            for dep in required_deps:
                if f'<artifactId>{dep}</artifactId>' not in content:
                    missing_deps.append(dep)
            
            if missing_deps:
                print(f"Missing dependencies: {', '.join(missing_deps)}")
                print("Creating new pom.xml with all required dependencies...")
                self._create_basic_pom(pom_path)
            else:
                print("All required dependencies already present")
                
        except Exception as e:
            print(f"Error checking pom.xml: {e}")
            print("Creating new pom.xml with required dependencies...")
            self._create_basic_pom(pom_path)

    def _create_basic_pom(self, pom_path: str) -> None:
        """Create a comprehensive pom.xml with all necessary Spring Boot dependencies"""
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
        <maven.compiler.source>17</maven.compiler.source>
        <maven.compiler.target>17</maven.compiler.target>
        <project.build.sourceEncoding>UTF-8</project.build.sourceEncoding>
    </properties>
    <dependencies>
        <!-- Spring Boot Web Starter -->
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-web</artifactId>
        </dependency>
        
        <!-- Spring Boot Data JPA Starter -->
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-data-jpa</artifactId>
        </dependency>
        
        <!-- Spring Boot Security Starter -->
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-security</artifactId>
        </dependency>
        
        <!-- Spring Boot Validation Starter -->
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-validation</artifactId>
        </dependency>
        
        <!-- Spring Boot Actuator Starter -->
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-actuator</artifactId>
        </dependency>
        
        <!-- Spring Boot Cache Starter -->
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-cache</artifactId>
        </dependency>
        
        <!-- Spring Boot Mail Starter -->
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-mail</artifactId>
        </dependency>
        
        <!-- H2 Database for development -->
        <dependency>
            <groupId>com.h2database</groupId>
            <artifactId>h2</artifactId>
            <scope>runtime</scope>
        </dependency>
        
        <!-- Spring Boot Test Starter -->
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-test</artifactId>
            <scope>test</scope>
        </dependency>
        
        <!-- Spring Security Test -->
        <dependency>
            <groupId>org.springframework.security</groupId>
            <artifactId>spring-security-test</artifactId>
            <scope>test</scope>
        </dependency>
        
        <!-- Jakarta Persistence API -->
        <dependency>
            <groupId>jakarta.persistence</groupId>
            <artifactId>jakarta.persistence-api</artifactId>
            <version>3.1.0</version>
        </dependency>
        
        <!-- Jakarta Validation API -->
        <dependency>
            <groupId>jakarta.validation</groupId>
            <artifactId>jakarta.validation-api</artifactId>
            <version>3.0.2</version>
        </dependency>
        
        <!-- Jackson for JSON processing -->
        <dependency>
            <groupId>com.fasterxml.jackson.core</groupId>
            <artifactId>jackson-databind</artifactId>
        </dependency>
        
        <!-- Spring Boot Configuration Processor -->
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-configuration-processor</artifactId>
            <optional>true</optional>
        </dependency>
        
        <!-- Spring Boot DevTools -->
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-devtools</artifactId>
            <scope>runtime</scope>
            <optional>true</optional>
        </dependency>
    </dependencies>
    <build>
        <plugins>
            <plugin>
                <groupId>org.springframework.boot</groupId>
                <artifactId>spring-boot-maven-plugin</artifactId>
                <configuration>
                    <excludes>
                        <exclude>
                            <groupId>org.springframework.boot</groupId>
                            <artifactId>spring-boot-configuration-processor</artifactId>
                        </exclude>
                    </excludes>
                </configuration>
            </plugin>
            <plugin>
                <groupId>org.apache.maven.plugins</groupId>
                <artifactId>maven-compiler-plugin</artifactId>
                <version>3.11.0</version>
                <configuration>
                    <source>17</source>
                    <target>17</target>
                    <encoding>UTF-8</encoding>
                </configuration>
            </plugin>
            <plugin>
                <groupId>org.apache.maven.plugins</groupId>
                <artifactId>maven-surefire-plugin</artifactId>
                <version>3.0.0</version>
            </plugin>
        </plugins>
    </build>
</project>'''
        
        with open(pom_path, 'w', encoding='utf-8') as f:
            f.write(basic_pom)
        print(f"Created comprehensive pom.xml with all required dependencies")

    def _create_application_yml(self, project_dir: str) -> None:
        """Create a basic application.yml with proper database configuration"""
        resources_dir = os.path.join(project_dir, "src", "main", "resources")
        os.makedirs(resources_dir, exist_ok=True)
        
        application_yml = '''server:
  port: 8080

spring:
  application:
    name: spring-project
  
  # Database Configuration
  datasource:
    url: jdbc:h2:mem:testdb
    driver-class-name: org.h2.Driver
    username: sa
    password: password
  
  # JPA Configuration
  jpa:
    hibernate:
      ddl-auto: create-drop
    show-sql: true
    properties:
      hibernate:
        dialect: org.hibernate.dialect.H2Dialect
        format_sql: true
  
  # H2 Console Configuration
  h2:
    console:
      enabled: true
      path: /h2-console
  
  # Security Configuration
  security:
    user:
      name: admin
      password: admin
  
  # Logging Configuration
  logging:
    level:
      org.springframework.security: DEBUG
      org.hibernate.SQL: DEBUG
      org.hibernate.type.descriptor.sql.BasicBinder: TRACE

# Actuator Configuration
management:
  endpoints:
    web:
      exposure:
        include: health,info,metrics
  endpoint:
    health:
      show-details: always

# Application specific configuration
app:
  name: Spring Boot Application
  version: 1.0.0
'''
        
        yml_path = os.path.join(resources_dir, "application.yml")
        with open(yml_path, 'w', encoding='utf-8') as f:
            f.write(application_yml)
        print(f"Created application.yml with proper configuration")

    def run(self, project_dir: str, output_dir: str) -> Dict[str, Any]:
        # Step 1: Structured chunking of legacy code
        print("Step 1: Performing structured chunking...")
        structures = self.structured_chunker.chunk_project(project_dir)
        print(f"Extracted {len(structures)} structural elements")

        # Step 2: Generate enhanced migration documentation with context preservation
        print("Step 2: Generating enhanced migration documentation...")
        migration_doc = self.enhanced_code_to_doc.run(structures)

        # Step 3: Evaluate documentation quality against legacy code
        print("Step 3: Evaluating documentation quality...")
        # Pass structures directly to evaluator for proper analysis
        evaluation = self.evaluator.run(migration_doc, structures, project_dir)

        # Step 4: Generate Spring Boot code based on evaluated documentation
        print("Step 4: Generating Spring Boot code...")
        # Get context snippets from structures
        context_snippets = [s.content for s in structures[:20]]
        spring_files = self.doc_to_spring.run(migration_doc, context_snippets, "data/workspace/knowledge_base.json")

        # Step 5: Generate project structure and write files
        print("Step 5: Writing Spring Boot project files...")
        temp_dir = tempfile.mkdtemp(prefix="springgen-")
        self._write_files(temp_dir, spring_files)

        # Step 6: Always create comprehensive pom.xml (overwrite any LLM-generated one)
        print("Step 6: Creating comprehensive pom.xml...")
        pom_path = os.path.join(temp_dir, "pom.xml")
        self._create_basic_pom(pom_path)
        
        # Step 6.5: Create application.yml if not present
        print("Step 6.5: Creating application.yml...")
        self._create_application_yml(temp_dir)

        # Step 7: Generate JUnit tests
        print("Step 7: Generating JUnit tests...")
        test_files = self.junit_gen.run(spring_files)
        self._write_files(temp_dir, test_files)

        # Step 8: Save outputs
        print("Step 8: Saving outputs...")
        os.makedirs(output_dir, exist_ok=True)
        with open(os.path.join(output_dir, "migration_doc.md"), "w", encoding="utf-8") as f:
            f.write(migration_doc)

        # Save evaluation results
        with open(os.path.join(output_dir, "evaluation.json"), "w", encoding="utf-8") as f:
            json.dump(evaluation, f, indent=2)

        # Step 9: Copy generated Spring Boot project
        project_name = os.path.basename(project_dir)
        spring_project_dir = os.path.join(output_dir, "spring_project")
        if os.path.exists(spring_project_dir):
            shutil.rmtree(spring_project_dir)
        shutil.copytree(temp_dir, spring_project_dir)

        # Cleanup
        shutil.rmtree(temp_dir)

        return {
            "project_dir": spring_project_dir,
            "migration_doc": migration_doc,
            "evaluation": evaluation,
            "spring_files": spring_files,
            "test_files": test_files,
            "structures_count": len(structures),
            "knowledge_base_path": "data/workspace/knowledge_base.json"
        }

