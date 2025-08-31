import io
import os
import sys
import time
import zipfile

CURRENT_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, os.pardir, os.pardir))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import streamlit as st

from app.config import settings
from app.ingestion.ingest import extract_zip_to_workspace
from app.packager.exporter import verify_maven_build, export_zip
from app.services.pipeline import ConversionPipeline


st.set_page_config(page_title="Legacy Java → Spring Boot Converter", layout="wide")
st.title("Legacy Java → Spring Boot Converter")

print("Streamlit app initialized.")  # Debugging

with st.sidebar:
    st.header("Settings")
    st.write("Make sure your Azure OpenAI credentials are set.")
    st.text_input("Endpoint", value=settings.azure_openai_endpoint, disabled=True)
    st.text_input("Deployment", value=settings.azure_openai_deployment, disabled=True)
    #st.text_input("Embedding", value=settings.embedding_deployment, disabled=True)

uploaded = st.file_uploader("Upload legacy Java source as ZIP", type=["zip"]) 
run_btn = st.button("Run Conversion", type="primary")

progress = st.progress(0)
status = st.empty()

if run_btn and uploaded is not None:
    print("Run button clicked and file uploaded.")  # Debugging
    progress.progress(5)
    status.info("Extracting and chunking (no embeddings)...")
    workspace = settings.workspace_dir
    print(f"Workspace directory: {workspace}")  # Debugging
    project_dir = extract_zip_to_workspace(uploaded.read(), workspace)
    print(f"Project directory after extraction: {project_dir}")  # Debugging

    pipeline = ConversionPipeline()
    progress.progress(20)
    status.info("Running Code → Document agent...")
    try:
        result = pipeline.run(project_dir, output_dir=os.path.join(workspace, "output"))
        print("Pipeline run completed successfully.")  # Debugging
    except Exception as e:
        progress.progress(40)
        status.error("Failed during conversion. Check your Azure configs or try again.")
        print(f"Error during pipeline run: {e}")  # Debugging
        st.exception(e)
        st.stop()

    progress.progress(70)
    status.info("Verifying Maven build...")
    ok, logs = verify_maven_build(result["project_dir"])
    print(f"Maven build verification status: {'Success' if ok else 'Failed'}")  # Debugging
    st.session_state["build_logs"] = logs

    progress.progress(85)
    status.info("Packaging ZIP...")
    zip_path = export_zip(result["project_dir"], os.path.join(workspace, "export", "spring_project.zip"))
    print(f"Exported ZIP path: {zip_path}")  # Debugging

    progress.progress(100)
    status.success("Done.")

    # Display results in vertical layout
    st.subheader("Migration Document")
    # Render unified final markdown directly
    st.markdown(result["migration_doc"]) 

    # Show enhanced metrics
    if "structures_count" in result:
        st.info(f"📊 **Structured Analysis**: Processed {result['structures_count']} structural elements")
    
    if "knowledge_base_path" in result:
        st.info(f"🧠 **Knowledge Base**: Available at {result['knowledge_base_path']}")

    st.subheader("Evaluation Dashboard")
    
    # Parse evaluation results
    evaluation = result.get("evaluation", {})
    
    # Create metrics dashboard
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        legacy_analysis = evaluation.get("legacy_code_analysis", {})
        structure = legacy_analysis.get("structure", {})
        total_files = structure.get("total_files", 0)
        java_files = structure.get("java_files", 0)
        st.metric("Total Files", total_files)
        if java_files > 0:
            st.caption(f"({java_files} Java files)")
    
    with col2:
        code_analysis = legacy_analysis.get("code_analysis", {})
        classes_detected = code_analysis.get("classes_detected", 0)
        methods_detected = code_analysis.get("methods_detected", 0)
        interfaces_detected = code_analysis.get("interfaces_detected", 0)
        enums_detected = code_analysis.get("enums_detected", 0)
        
        total_components = classes_detected + methods_detected + interfaces_detected + enums_detected
        component_text = f"{classes_detected} classes, {methods_detected} methods"
        if interfaces_detected > 0:
            component_text += f", {interfaces_detected} interfaces"
        if enums_detected > 0:
            component_text += f", {enums_detected} enums"
        
        st.metric("Components", component_text)
        st.caption(f"Total: {total_components} elements")
    
    with col3:
        complexity_score = structure.get("complexity_score", 0)
        st.metric("Complexity Score", f"{complexity_score:.1f}/10")
        if complexity_score > 7:
            st.caption("⚠️ High complexity")
        elif complexity_score > 4:
            st.caption("⚠️ Moderate complexity")
        else:
            st.caption("✅ Low complexity")
    
    with col4:
        total_code_size = code_analysis.get("total_code_size", 0)
        st.metric("Code Size", f"{total_code_size:,} chars")
        if total_code_size > 100000:
            st.caption("📁 Large codebase")
        elif total_code_size > 50000:
            st.caption("📁 Medium codebase")
        else:
            st.caption("📁 Small codebase")
    
    # Overall status
    summary = evaluation.get("summary", {})
    overall_status = summary.get("overall_status", "UNKNOWN")
    
    if overall_status == "PASS":
        st.success("🎉 Documentation Quality: PASS")
    elif overall_status == "FAIL":
        st.error("⚠️ Documentation Quality: FAIL")
    else:
        st.warning("⚠️ Documentation Quality: UNKNOWN")
    
    # Enhanced evaluation sections
    with st.expander("📊 Enhanced Evaluation Report", expanded=True):
        tab1, tab2, tab3, tab4 = st.tabs(["Legacy Code Analysis", "Documentation Quality", "Migration Readiness", "Dependency Analysis"])
        
        with tab1:
            st.write("### Legacy Code Structure Analysis")
            if structure:
                st.write(f"**Total Files:** {structure.get('total_files', 0)}")
                st.write(f"**Java Files:** {structure.get('java_files', 0)}")
                st.write(f"**Total Code Size:** {structure.get('total_code_size', 0):,} characters")
                st.write(f"**Classes Detected:** {structure.get('classes_detected', 0)}")
                st.write(f"**Methods Detected:** {structure.get('methods_detected', 0)}")
                st.write(f"**Interfaces Detected:** {structure.get('interfaces_detected', 0)}")
                st.write(f"**Enums Detected:** {structure.get('enums_detected', 0)}")
                st.write(f"**Complexity Score:** {structure.get('complexity_score', 0):.1f}/10")
                st.write(f"**Average Dependencies:** {structure.get('avg_dependencies', 0):.2f}")
            
            st.write("### Code Analysis Results")
            if code_analysis:
                st.write(f"**Total Chunks Processed:** {code_analysis.get('total_chunks', 0)}")
                st.write(f"**Classes Detected:** {code_analysis.get('classes_detected', 0)}")
                st.write(f"**Methods Detected:** {code_analysis.get('methods_detected', 0)}")
                st.write(f"**Interfaces Detected:** {code_analysis.get('interfaces_detected', 0)}")
                st.write(f"**Enums Detected:** {code_analysis.get('enums_detected', 0)}")
                st.write(f"**Complexity Score:** {code_analysis.get('complexity_score', 0):.1f}/10")
                st.write(f"**Total Code Size:** {code_analysis.get('total_code_size', 0):,} characters")
                st.write(f"**Average Dependencies:** {code_analysis.get('avg_dependencies', 0):.2f}")
        
        with tab2:
            st.write("### Documentation Quality Assessment")
            quality_assessment = evaluation.get("documentation_quality_assessment")
            if quality_assessment:
                if isinstance(quality_assessment, dict):
                    st.write("**Overall Score:**", quality_assessment.get("overall_score", "N/A"))
                    st.write("**Status:**", quality_assessment.get("status", "N/A"))
                    
                    # Documentation completeness
                    doc_completeness = quality_assessment.get("documentation_completeness", 0)
                    st.progress(doc_completeness / 100)
                    st.write(f"Documentation Completeness: {doc_completeness}%")
                    
                    # Technical accuracy
                    tech_accuracy = quality_assessment.get("technical_accuracy", 0)
                    st.progress(tech_accuracy / 100)
                    st.write(f"Technical Accuracy: {tech_accuracy}%")
                    
                    # Business logic coverage
                    bl_coverage = quality_assessment.get("business_logic_coverage", 0)
                    st.progress(bl_coverage / 100)
                    st.write(f"Business Logic Coverage: {bl_coverage}%")
                    
                    # Critical issues
                    critical_issues = quality_assessment.get("critical_issues", [])
                    if critical_issues:
                        st.write("**Critical Issues:**")
                        for issue in critical_issues:
                            st.error(f"🔴 {issue.get('component', 'Unknown')}: {issue.get('issue', 'Unknown issue')}")
                    
                    # Recommendations
                    recommendations = quality_assessment.get("recommendations", [])
                    if recommendations:
                        st.write("**Recommendations:**")
                        for rec in recommendations:
                            st.info(f"💡 {rec}")
                else:
                    st.write("Quality assessment data available but not in expected format")
            else:
                st.warning("No quality assessment data available")
        
        with tab3:
            st.write("### Migration Readiness Assessment")
            if quality_assessment and isinstance(quality_assessment, dict):
                migration_readiness = quality_assessment.get("migration_readiness", 0)
                st.progress(migration_readiness / 100)
                st.write(f"Migration Readiness: {migration_readiness}%")
                
                if migration_readiness >= 80:
                    st.success("✅ Ready for Spring Boot code generation")
                elif migration_readiness >= 60:
                    st.warning("⚠️ Some improvements needed before code generation")
                else:
                    st.error("❌ Significant documentation improvements required")
        
        with tab4:
            st.write("### Dependency Analysis")
            if "structures_count" in result:
                st.write(f"**Structured Elements Processed:** {result['structures_count']}")
                st.write("**Dependency Graph:** Built and analyzed")
                st.write("**Knowledge Base:** Generated with component relationships")
                
                # Show some dependency insights
                if structure:
                    avg_deps = structure.get("avg_dependencies", 0)
                    st.write(f"**Average Dependencies:** {avg_deps:.2f}")
                    
                    if avg_deps > 5:
                        st.warning("⚠️ High dependency complexity detected")
                    elif avg_deps > 2:
                        st.info("ℹ️ Moderate dependency complexity")
                    else:
                        st.success("✅ Low dependency complexity")
    
    # Component Analysis Section
    st.subheader("🔍 Component Analysis")
    
    # Try to get component summaries from the migration document
    migration_doc = result.get("migration_doc", "")
    
    # Extract component summaries from the migration document
    component_sections = []
    lines = migration_doc.split('\n')
    current_component = None
    current_content = []
    
    for line in lines:
        if line.startswith('### ') and ('Class:' in line or 'Method:' in line or 'Interface:' in line or 'Enum:' in line):
            if current_component:
                component_sections.append((current_component, '\n'.join(current_content)))
            current_component = line.strip()
            current_content = []
        elif current_component and line.strip():
            current_content.append(line)
    
    if current_component:
        component_sections.append((current_component, '\n'.join(current_content)))
    
    if component_sections:
        for component_header, component_content in component_sections[:10]:  # Show first 10 components
            with st.expander(component_header, expanded=False):
                # Parse component details
                lines = component_content.split('\n')
                purpose = "N/A"
                business_rules = []
                inputs = []
                outputs = []
                dependencies = []
                complexity_score = "N/A"
                
                for line in lines:
                    line = line.strip()
                    if line.startswith('- **Purpose**:'):
                        purpose = line.replace('- **Purpose**:', '').strip()
                    elif line.startswith('- **Business Rules**:'):
                        rules_text = line.replace('- **Business Rules**:', '').strip()
                        if rules_text != 'None':
                            business_rules = [rule.strip() for rule in rules_text.split(',')]
                    elif line.startswith('- **Inputs**:'):
                        inputs_text = line.replace('- **Inputs**:', '').strip()
                        if inputs_text != 'None':
                            inputs = [input_item.strip() for input_item in inputs_text.split(',')]
                    elif line.startswith('- **Outputs**:'):
                        outputs_text = line.replace('- **Outputs**:', '').strip()
                        if outputs_text != 'None':
                            outputs = [output_item.strip() for output_item in outputs_text.split(',')]
                    elif line.startswith('- **Dependencies**:'):
                        deps_text = line.replace('- **Dependencies**:', '').strip()
                        if deps_text != 'None':
                            dependencies = [dep.strip() for dep in deps_text.split(',')]
                    elif line.startswith('- **Complexity Score**:'):
                        complexity_score = line.replace('- **Complexity Score**:', '').strip()
                
                # Display component details
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.write(f"**Purpose:** {purpose}")
                    
                    if business_rules:
                        st.write("**Business Rules:**")
                        for rule in business_rules:
                            st.write(f"• {rule}")
                    else:
                        st.write("**Business Rules:** None")
                    
                    if inputs:
                        st.write("**Inputs:**")
                        for input_item in inputs:
                            st.write(f"• {input_item}")
                    else:
                        st.write("**Inputs:** None")
                    
                    if outputs:
                        st.write("**Outputs:**")
                        for output_item in outputs:
                            st.write(f"• {output_item}")
                    else:
                        st.write("**Outputs:** None")
                
                with col2:
                    if dependencies:
                        st.write("**Dependencies:**")
                        for dep in dependencies:
                            st.write(f"• {dep}")
                    else:
                        st.write("**Dependencies:** None")
                    
                    st.write(f"**Complexity Score:** {complexity_score}")
    else:
        st.warning("No component analysis available. The migration document may not contain structured component summaries.")

    # Manual review requirements
    if evaluation.get("documentation_quality_assessment", {}).get("manual_review_required"):
        st.subheader("🔍 Manual Review Required")
        for review_item in evaluation["documentation_quality_assessment"]["manual_review_required"]:
            priority = review_item.get("priority", "MEDIUM")
            if priority == "HIGH":
                st.error(f"🔴 {review_item.get('area', 'Unknown')}: {review_item.get('reason', 'No reason provided')}")
            else:
                st.warning(f"🟡 {review_item.get('area', 'Unknown')}: {review_item.get('reason', 'No reason provided')}")

    st.subheader("Spring Boot Code (generated)")
    if result.get("spring_files"):
        for f in result["spring_files"]:
            with st.expander(f.get("path", "(no path)")):
                st.code(f.get("content", ""), language="java" if f.get("path", "").endswith(".java") else None)
    else:
        st.write("No Spring files generated.")

    st.subheader("JUnit Test Cases (generated)")
    if result.get("test_files"):
        for f in result["test_files"]:
            with st.expander(f.get("path", "(no path)")):
                st.code(f.get("content", ""), language="java" if f.get("path", "").endswith(".java") else None)
    else:
        st.write("No test files generated.")

    st.subheader("Build Status")
    st.write("Success" if ok else "Failed")
    with st.expander("Maven Logs"):
        st.code(st.session_state.get("build_logs", ""))

    st.download_button(
        label="Download Spring Boot ZIP",
        data=open(zip_path, "rb").read(),
        file_name="spring_project.zip",
        mime="application/zip",
    )
    print("Download button rendered.")  # Debugging

elif uploaded is None:
    st.info("Upload a ZIP of your legacy Java project to begin.")
