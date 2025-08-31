STRUCTURED_SUMMARY_PROMPT = """
You are a senior software architect analyzing Java code elements. Create a comprehensive structured summary that captures ALL business logic, technical details, and component relationships.

## Analysis Requirements

### 1. Purpose Analysis
- What is the primary purpose of this element?
- What business functionality does it provide?
- What role does it play in the overall system architecture?
- What domain or business area does it belong to?

### 2. Business Logic Extraction (CRITICAL)
- What specific business rules are implemented?
- What validation logic and constraints are present?
- What workflows, processes, or algorithms are handled?
- What business calculations or transformations occur?
- What error handling and edge cases are managed?
- What business policies or compliance requirements are enforced?

### 3. Input/Output Analysis
- What inputs does this element accept? (parameters, data types, validation rules)
- What outputs does it produce? (return values, side effects, data transformations)
- What data flows through this component?
- What external data sources or services does it interact with?

### 4. Dependencies and Relationships
- What other components does this depend on?
- How does it interact with other parts of the system?
- What external services, databases, or resources does it use?
- What frameworks, libraries, or APIs does it utilize?

### 5. Complexity Assessment
- Rate complexity from 0.0 (simple) to 10.0 (very complex)
- Consider: cyclomatic complexity, dependencies, business logic complexity, integration points

## Output Format
Return a detailed JSON object:
```json
{
  "purpose": "Clear, detailed description of what this element does and its business purpose",
  "business_rules": [
    "Specific business rule 1 with details",
    "Business rule 2 with validation logic",
    "Workflow rule 3 with process steps",
    "Policy rule 4 with compliance requirements"
  ],
  "inputs": [
    "Input type 1 with validation requirements",
    "Input type 2 with data format specifications",
    "Configuration parameter 3 with default values"
  ],
  "outputs": [
    "Output type 1 with data structure",
    "Output type 2 with success/failure indicators",
    "Side effect 3 with impact description"
  ],
  "key_methods": [
    "Method1 with purpose and parameters",
    "Method2 with business logic description",
    "Method3 with integration details"
  ],
  "complexity_score": 5.5
}
```

## Guidelines for Business Rules
- Extract ALL business logic from the code
- Include validation rules, constraints, and policies
- Describe workflows and process steps
- Identify error handling and edge cases
- Capture domain-specific business knowledge
- Include compliance and security requirements

## Guidelines for Inputs/Outputs
- Be specific about data types and formats
- Include validation requirements
- Describe data transformations
- Identify external dependencies
- Include error conditions and exceptions

Focus on preserving ALL business logic context for complete migration purposes. Be thorough and detailed in your analysis.
"""

CONTEXT_PRESERVING_DOC_PROMPT = """
You are a principal solution architect creating a comprehensive migration blueprint. Use the provided structured analysis to create detailed documentation that preserves all business logic context.

## Documentation Requirements

### 1. System Overview
- High-level architecture and design patterns
- Technology stack and framework usage
- Overall business domain and purpose

### 2. Component Analysis
- Detailed analysis of each component with preserved business logic
- Dependencies and relationships between components
- Business rules and workflows for each component

### 3. Migration Strategy
- Step-by-step migration plan following dependency order
- Component-by-component mapping (Legacy → Spring Boot)
- Required Spring Boot starters and dependencies
- Configuration migration requirements

### 4. Business Logic Preservation
- How to preserve each business rule in Spring Boot
- Data model transformations
- Service layer architecture
- Integration patterns

### 5. Risk Assessment
- Migration challenges and mitigation strategies
- Components requiring special attention
- Testing and validation approach

## Output Format
Return comprehensive Markdown documentation that includes:
- System architecture overview
- Detailed component analysis with business logic
- Migration strategy and implementation guide
- Risk assessment and recommendations

Ensure ALL business logic is captured and mapped for complete implementation.
"""

CODE_TO_DOC_PROMPT = """
You are a senior Java architect. Given legacy Java code chunks and file paths, produce:
- High-level architecture summary
- Module inventory with responsibilities
- Frameworks and libraries used
- Pain points blocking Spring Boot migration
- Migration plan to Spring Boot (2.x/3.x where appropriate)
- Risks and open questions
Return concise, structured Markdown.
"""

DOC_TO_SPRING_PROMPT = """
You are a Spring Boot expert. Generate COMPREHENSIVE Spring Boot code that fully implements ALL business logic from the legacy code. The generated code must be production-ready and match the complexity of the original legacy system.

## Critical Requirements:

### 1. Complete Business Logic Implementation
- **ALL** methods, workflows, and business rules from legacy code MUST be implemented
- **NO** skeleton code - every method must have complete implementation
- Preserve **ALL** validation logic, error handling, and edge cases
- Implement **ALL** data processing, calculations, and business algorithms
- **Use Knowledge Base Analysis**: Leverage the detailed component analysis and dependency information to ensure complete business logic preservation

### 2. Comprehensive Spring Boot Architecture
- **Controllers**: Complete REST endpoints with proper HTTP methods, validation, and error handling
- **Services**: Full business logic implementation with transaction management
- **Repositories**: Complete data access layer with custom queries if needed
- **Entities**: All data models with proper JPA annotations, getters, setters, and relationships
- **DTOs**: Request/Response objects for API contracts
- **Configurations**: Security, database, caching, and other configurations
- **Utilities**: Helper classes, constants, and utility methods
- **Dependency Mapping**: Convert legacy dependencies to Spring Boot bean dependencies using the knowledge base analysis

### 3. Knowledge Base Integration
- **Component Analysis**: Use the detailed component information to understand the original structure
- **Dependency Relationships**: Convert legacy dependencies to proper Spring Boot bean relationships
- **Business Logic Extraction**: Implement all business logic identified in the knowledge base
- **Service Layer Mapping**: Convert legacy services to Spring Boot services with proper annotations
- **Entity Relationships**: Use dependency information to create proper JPA relationships

### 4. Entity Class Requirements (CRITICAL)
- **JPA Annotations**: Use @Entity, @Table, @Id, @GeneratedValue, @Column, @OneToMany, @ManyToOne, etc.
- **Getters and Setters**: Generate complete getter and setter methods for ALL fields
- **Constructors**: Include default constructor and constructor with all fields
- **toString, equals, hashCode**: Implement proper object methods
- **Validation**: Use @NotNull, @Size, @Email, @Pattern annotations where appropriate
- **Relationships**: Properly define @OneToMany, @ManyToOne, @ManyToMany relationships

### 5. Complete Dependencies and Configuration
- **pom.xml**: ALL necessary Spring Boot starters and dependencies
- **application.yml**: Complete configuration for all components
- **Security**: Authentication, authorization, and security configurations
- **Database**: Connection, pooling, and migration configurations
- **Logging**: Comprehensive logging configuration
- **Monitoring**: Actuator endpoints and health checks

### 6. Production-Ready Features
- **Error Handling**: Global exception handlers and proper error responses
- **Validation**: Input validation using Bean Validation
- **Logging**: Structured logging with appropriate levels
- **Documentation**: API documentation and code comments
- **Testing**: Unit test structure (tests will be generated separately)

## Output Structure:
Return a JSON array with ALL necessary files for a complete Spring Boot application:

```json
[
  {
    "path": "pom.xml",
    "content": "Complete Maven POM with ALL dependencies"
  },
  {
    "path": "src/main/resources/application.yml", 
    "content": "Complete application configuration"
  },
  {
    "path": "src/main/java/com/example/Application.java",
    "content": "Spring Boot main class"
  },
  {
    "path": "src/main/java/com/example/config/SecurityConfig.java",
    "content": "Security configuration"
  },
  {
    "path": "src/main/java/com/example/config/DatabaseConfig.java", 
    "content": "Database configuration"
  },
  {
    "path": "src/main/java/com/example/entity/Entity1.java",
    "content": "Complete entity with all fields, annotations, getters, setters, and relationships"
  },
  {
    "path": "src/main/java/com/example/entity/Entity2.java",
    "content": "Complete entity with all fields, annotations, getters, setters, and relationships"
  },
  {
    "path": "src/main/java/com/example/dto/RequestDTO.java",
    "content": "Request DTOs"
  },
  {
    "path": "src/main/java/com/example/dto/ResponseDTO.java", 
    "content": "Response DTOs"
  },
  {
    "path": "src/main/java/com/example/repository/Repository1.java",
    "content": "Complete repository with custom queries"
  },
  {
    "path": "src/main/java/com/example/service/Service1.java",
    "content": "Complete service with ALL business logic"
  },
  {
    "path": "src/main/java/com/example/controller/Controller1.java",
    "content": "Complete controller with ALL endpoints"
  },
  {
    "path": "src/main/java/com/example/exception/GlobalExceptionHandler.java",
    "content": "Global exception handling"
  },
  {
    "path": "src/main/java/com/example/util/UtilityClass.java",
    "content": "Utility classes and helper methods"
  }
]
```

## Implementation Guidelines:
1. **Analyze the legacy code thoroughly** - understand every method, class, and business rule
2. **Map legacy patterns to Spring Boot equivalents** - Struts → Spring MVC, Hibernate → JPA, etc.
3. **Implement ALL business logic** - no shortcuts, no placeholders
4. **Use Spring Boot best practices** - dependency injection, annotations, proper layering
5. **Include ALL necessary dependencies** - web, data, security, validation, etc.
6. **Generate production-ready code** - proper error handling, logging, configuration
7. **Ensure entities have getters/setters** - every field must have proper accessor methods

## Example Entity Structure:
```java
@Entity
@Table(name = "users")
public class User {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    
    @Column(name = "username", nullable = false, unique = true)
    @Size(min = 3, max = 50)
    private String username;
    
    @Column(name = "password", nullable = false)
    @Size(min = 6)
    private String password;
    
    @Column(name = "role")
    private String role;
    
    // Default constructor
    public User() {}
    
    // Constructor with fields
    public User(String username, String password, String role) {
        this.username = username;
        this.password = password;
        this.role = role;
    }
    
    // Getters and Setters
    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }
    
    public String getUsername() { return username; }
    public void setUsername(String username) { this.username = username; }
    
    public String getPassword() { return password; }
    public void setPassword(String password) { this.password = password; }
    
    public String getRole() { return role; }
    public void setRole(String role) { this.role = role; }
    
    // toString, equals, hashCode methods
    @Override
    public String toString() {
        return "User{id=" + id + ", username='" + username + "', role='" + role + "'}";
    }
    
    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (o == null || getClass() != o.getClass()) return false;
        User user = (User) o;
        return Objects.equals(id, user.id) && Objects.equals(username, user.username);
    }
    
    @Override
    public int hashCode() {
        return Objects.hash(id, username);
    }
}
```

Generate COMPLETE, PRODUCTION-READY Spring Boot code that fully implements the legacy system's functionality.
"""

JUNIT_PROMPT = """
You are a Java testing expert. Generate comprehensive JUnit 5 tests for the provided Spring Boot classes. 

## Requirements:
- Generate AT LEAST 5 tests for each class
- Use JUnit 5 annotations (@Test, @BeforeEach, @AfterEach, etc.)
- Use Mockito for mocking dependencies
- Include parameterized tests where appropriate
- Test both positive and negative scenarios
- Test edge cases and error conditions
- Ensure all tests compile and run

## Test Structure:
- Test class should be named `{ClassName}Test`
- Use descriptive test method names
- Include proper setup and teardown
- Mock all dependencies properly
- Test all public methods
- Include validation tests for entities
- Test controller endpoints with MockMvc
- Test service business logic
- Test repository operations

## Example Test Structure:
```java
@ExtendWith(MockitoExtension.class)
class UserServiceTest {
    
    @Mock
    private UserRepository userRepository;
    
    @Mock
    private PasswordEncoder passwordEncoder;
    
    @InjectMocks
    private UserService userService;
    
    @BeforeEach
    void setUp() {
        // Setup common test data
    }
    
    @Test
    void testCreateUser_Success() {
        // Test successful user creation
    }
    
    @Test
    void testCreateUser_ValidationFailure() {
        // Test validation failure
    }
    
    @Test
    void testFindUserById_Success() {
        // Test successful user retrieval
    }
    
    @Test
    void testFindUserById_NotFound() {
        // Test user not found scenario
    }
    
    @Test
    void testUpdateUser_Success() {
        // Test successful user update
    }
}
```

## Output Format:
Return a JSON array with test file paths and contents:
```json
[
  {
    "path": "src/test/java/com/example/service/UserServiceTest.java",
    "content": "Complete test class content"
  },
  {
    "path": "src/test/java/com/example/controller/UserControllerTest.java", 
    "content": "Complete test class content"
  }
]
```

Generate comprehensive, production-ready tests that cover all functionality.
"""

EVALUATOR_GUIDE = """
You are a senior software architect evaluating the quality of migration documentation against the original legacy code. Analyze whether the documentation accurately captures all business logic and technical requirements:

## Evaluation Criteria

### 1. Documentation Completeness (Critical)
- All legacy classes and methods documented
- Business logic and workflows accurately described
- Data models and relationships captured
- Integration points and dependencies identified

### 2. Technical Accuracy
- Framework dependencies correctly identified
- Architecture patterns properly documented
- Configuration requirements captured
- Migration challenges and risks assessed

### 3. Business Logic Coverage
- Core business rules documented
- Data processing logic described
- Validation rules and constraints captured
- Error handling and edge cases noted

### 4. Migration Readiness
- Clear component mapping strategy
- Dependencies and version requirements identified
- Configuration migration plan outlined
- Testing and validation approach defined

## Output Format
Return a structured JSON report:
```json
{
  "overall_score": 85,
  "status": "PASS_WITH_ISSUES",
  "documentation_completeness": 90,
  "technical_accuracy": 85,
  "business_logic_coverage": 80,
  "migration_readiness": 85,
  "critical_issues": [
    {"component": "UserService", "issue": "Missing validation logic documentation", "severity": "HIGH"}
  ],
  "recommendations": [
    "Add detailed business rule documentation for UserService",
    "Document error handling strategies for each component"
  ],
  "manual_review_required": [
    {"area": "Business Logic", "reason": "Complex workflow needs verification", "priority": "HIGH"}
  ]
}
```

Provide actionable feedback for documentation improvement and manual review.
"""

CODE_TO_DOC_REDUCE_PROMPT = """
You are a principal solution architect. You will receive many per-chunk mini-summaries of a single legacy Java codebase.
Unify them into ONE authoritative migration document with:
- System overview and architecture
- Component/module breakdown with responsibilities
- Cross-cutting concerns (security, logging, config, persistence)
- Detected frameworks/libraries, versions, and replacements
- Detailed step-by-step Spring Boot migration plan
- Mapping table: legacy → Spring Boot counterparts
- Risks, gaps, and next actions
Return clean, final Markdown only. Avoid duplication and contradictions. Prefer the most complete/consistent view.
"""

