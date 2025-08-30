## Legacy Java to Spring Boot Converter (GenAI + Azure OpenAI + FAISS)

This project converts legacy Java codebases into Spring Boot projects using a multi-agent GenAI pipeline powered by Azure OpenAI and FAISS vector search. It provides a Streamlit UI for upload, progress tracking, previews, evaluation dashboards, and a final ZIP export verified with a Maven build.

### Key Features
- Streamlit UI with progress bar, previews, and dashboard
- Ingestion and chunking of Java sources; indexed with FAISS
- Code-to-Document agent to produce architectural docs and migration guides
- Evaluator agent integrates javalang, tree-sitter, and SpotBugs
- Document-to-Spring Boot code generator agent
- JUnit test generator agent
- Storage of generated docs, sources, and tests; export to ZIP
- Optional Dockerized runtime

### Architecture
- `app/ingestion`: file upload, preprocessing, chunking
- `app/vectorstore`: FAISS index and semantic search
- `app/clients`: Azure OpenAI client wrapper
- `app/agents`: Code→Doc, Evaluator, Doc→Spring, JUnit agents
- `app/services`: Orchestration pipeline to run end-to-end
- `app/packager`: Maven build verification and ZIP export
- `app/ui`: Streamlit application

### Prerequisites
- Python 3.10+
- Java 17+ and Maven 3.9+
- Node.js (optional, for tree-sitter CLI grammar builds) or prebuilt Python bindings
- FAISS CPU (via pip)
- Azure OpenAI resource and deployment

### Quickstart (Local)
1. Create `.env` from template:
```bash
cp .env.example .env
# Fill in AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_KEY, AZURE_OPENAI_DEPLOYMENT, AZURE_OPENAI_API_VERSION
```
2. Create virtual env and install deps:
```bash
python -m venv .venv
. .venv/bin/activate  # On Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
```
3. Run Streamlit app:
```bash
streamlit run app/ui/streamlit_app.py
```

### Docker (Optional)
```bash
docker build -t java-spring-converter .
docker run --rm -p 8501:8501 --env-file .env -v ${PWD}/data:/workspace/data java-spring-converter
```

### Pipeline
1. Upload legacy Java code ZIP or folder
2. Ingestion: extract, read, normalize, chunk, and index to FAISS
3. Code→Doc agent generates architecture and migration docs
4. Evaluator runs static checks (javalang, tree-sitter, SpotBugs)
5. Doc→Spring agent produces Spring Boot modules and skeleton
6. JUnit agent writes tests
7. Store outputs and verify build with Maven
8. Export as ZIP

### Configuration
- `app/config.py` reads env vars (see `.env.example`).

### Testing
```bash
pytest -q
```

### Notes
- For SpotBugs, Java must be installed. The Docker image includes OpenJDK and Maven.
- If tree-sitter Java grammar build fails, the evaluator gracefully degrades to javalang checks.


