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

    # Vertical layout in requested order
    st.subheader("Migration Document")
    # Render unified final markdown directly
    st.markdown(result["migration_doc"]) 

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
    
    with col2:
        syntax_validation = legacy_analysis.get("syntax_validation", {})
        total_chunks = syntax_validation.get("total_chunks", 0)
        valid_chunks = syntax_validation.get("valid_chunks", 0)
        syntax_score = (valid_chunks / max(total_chunks, 1)) * 100
        st.metric("Syntax Score", f"{syntax_score:.1f}%")
    
    with col3:
        complexity_score = structure.get("complexity_score", 0)
        st.metric("Complexity Score", f"{complexity_score:.1f}/10")
    
    with col4:
        classes_detected = structure.get("classes_detected", 0)
        methods_detected = structure.get("methods_detected", 0)
        st.metric("Components", f"{classes_detected} classes, {methods_detected} methods")
    
    # Overall status
    summary = evaluation.get("summary", {})
    overall_status = summary.get("overall_status", "UNKNOWN")
    
    if overall_status == "PASS":
        st.success("🎉 Documentation Quality: PASS")
    elif overall_status == "FAIL":
        st.error("⚠️ Documentation Quality: FAIL")
    else:
        st.warning("⚠️ Documentation Quality: UNKNOWN")
    
    # Detailed evaluation sections
    with st.expander("📊 Detailed Evaluation Report", expanded=True):
        tab1, tab2, tab3 = st.tabs(["Legacy Code Analysis", "Documentation Quality", "Migration Readiness"])
        
        with tab1:
            st.write("### Legacy Code Structure Analysis")
            if structure:
                st.write(f"**Total Files:** {structure.get('total_files', 0)}")
                st.write(f"**Java Files:** {structure.get('java_files', 0)}")
                st.write(f"**Total Code Size:** {structure.get('total_code_size', 0):,} characters")
                st.write(f"**Classes Detected:** {structure.get('classes_detected', 0)}")
                st.write(f"**Methods Detected:** {structure.get('methods_detected', 0)}")
                st.write(f"**Complexity Score:** {structure.get('complexity_score', 0):.1f}/10")
            
            st.write("### Syntax Validation Results")
            if syntax_validation.get("details"):
                for detail in syntax_validation["details"]:
                    if detail.get("syntax"):
                        st.success(f"✅ {detail.get('file', 'Unknown')} (chunk {detail.get('chunk_index', 'N/A')}): Valid syntax")
                    else:
                        st.error(f"❌ {detail.get('file', 'Unknown')} (chunk {detail.get('chunk_index', 'N/A')}): {detail.get('error', 'Unknown error')}")
        
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
