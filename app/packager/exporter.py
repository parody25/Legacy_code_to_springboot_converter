import os
import shutil
import subprocess
import zipfile
from typing import Tuple, List

from app.config import settings


def _resolve_maven_command(project_dir: str) -> List[str]:
    """Resolve the best available Maven command for the environment"""
    # Prefer project wrapper if present
    mvnw_sh = os.path.join(project_dir, "mvnw")
    mvnw_cmd = os.path.join(project_dir, "mvnw.cmd")
    
    if os.path.isfile(mvnw_cmd):
        print(f"Using Maven wrapper: {mvnw_cmd}")
        return [mvnw_cmd]
    if os.path.isfile(mvnw_sh):
        print(f"Using Maven wrapper: {mvnw_sh}")
        return [mvnw_sh]
    
    # Try configured maven bin
    if settings.maven_bin and shutil.which(settings.maven_bin):
        print(f"Using configured Maven: {settings.maven_bin}")
        return [settings.maven_bin]
    
    # Try common Windows Maven installations
    if os.name == "nt":
        # Check common Windows Maven paths
        common_paths = [
            "mvn.cmd",
            "mvn",
            r"C:\Program Files\Apache\maven\bin\mvn.cmd",
            r"C:\apache-maven\bin\mvn.cmd",
            os.path.expanduser(r"~\apache-maven\bin\mvn.cmd")
        ]
        
        for mvn_path in common_paths:
            if shutil.which(mvn_path):
                print(f"Using Maven: {mvn_path}")
                return [mvn_path]
    
    # Try system PATH
    if shutil.which("mvn"):
        print("Using system Maven: mvn")
        return ["mvn"]
    
    # As a last resort, return configured value (will likely fail but produce clear error)
    print(f"Warning: Using potentially invalid Maven path: {settings.maven_bin}")
    return [settings.maven_bin]


def verify_maven_build(project_dir: str) -> Tuple[bool, str]:
    """Verify that the generated project can be built with Maven"""
    try:
        mvn = _resolve_maven_command(project_dir)
        cmd = mvn + ["-q", "-DskipTests", "clean", "compile"]
        
        print(f"Running Maven command: {' '.join(cmd)}")
        print(f"Working directory: {project_dir}")
        
        # Check if project directory exists and contains pom.xml
        if not os.path.exists(project_dir):
            return False, f"Project directory does not exist: {project_dir}"
        
        pom_files = [f for f in os.listdir(project_dir) if f == "pom.xml"]
        if not pom_files:
            return False, f"No pom.xml found in {project_dir}"
        
        proc = subprocess.run(
            cmd, 
            cwd=project_dir, 
            capture_output=True, 
            text=True, 
            check=False,
            timeout=300  # 5 minute timeout
        )
        
        ok = proc.returncode == 0
        output = proc.stdout + "\n" + proc.stderr
        
        if not ok:
            output = f"Maven build failed (exit code: {proc.returncode})\n{output}"
        
        return ok, output
        
    except subprocess.TimeoutExpired:
        return False, "Maven build timed out after 5 minutes"
    except FileNotFoundError:
        return False, f"Maven command not found. Please ensure Maven is installed and in PATH, or use mvnw wrapper."
    except Exception as e:
        return False, f"Maven build error: {str(e)}"


def export_zip(project_dir: str, dest_zip: str) -> str:
    """Export the generated project as a ZIP file"""
    os.makedirs(os.path.dirname(dest_zip), exist_ok=True)
    if os.path.exists(dest_zip):
        os.remove(dest_zip)
    
    with zipfile.ZipFile(dest_zip, 'w', zipfile.ZIP_DEFLATED) as zf:
        for base, _, files in os.walk(project_dir):
            for f in files:
                path = os.path.join(base, f)
                arc = os.path.relpath(path, project_dir)
                zf.write(path, arc)
    
    return dest_zip

