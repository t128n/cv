from ruamel.yaml import YAML
import shutil
from pathlib import Path
import subprocess
import sys
import os

def log(message, symbol="ℹ️"):
    print(f"{symbol} {message}")

def render():
    # 1. Load the name from resume.yaml
    resume_path = Path("resume.yaml")
    if not resume_path.exists():
        log(f"Error: {resume_path} not found.", "❌")
        sys.exit(1)

    log(f"Loading resume data from {resume_path}...")
    yaml = YAML(typ='safe')
    with open(resume_path, "r") as f:
        data = yaml.load(f)
    
    name = data["cv"]["name"]
    # RenderCV replaces spaces with underscores for the default filename
    safe_name = name.replace(" ", "_")
    
    output_dir = Path("rendercv_output")
    dist_dir = Path("dist")
    
    # 2. Run RenderCV
    log(f"Rendering resume for {name} using RenderCV...", "🚀")
    try:
        subprocess.run(["rendercv", "render", str(resume_path)], check=True)
    except subprocess.CalledProcessError as e:
        log(f"RenderCV failed with error: {e}", "❌")
        sys.exit(1)
    
    # 3. Move and rename files
    log(f"Ensuring distribution directory {dist_dir} exists...", "📂")
    dist_dir.mkdir(parents=True, exist_ok=True)

    mapping = {
        f"{safe_name}_CV.pdf": dist_dir / "Torben-Haack.pdf",
        f"{safe_name}_CV.md": Path("README.md"),
    }
    
    for src_name, dest_path in mapping.items():
        src_path = output_dir / src_name
        if src_path.exists():
            log(f"Moving {src_path} to {dest_path}...", "📦")
            shutil.copy2(src_path, dest_path)
        else:
            log(f"Warning: Could not find {src_path} in {output_dir}", "⚠️")

    # 4. Cleanup
    if output_dir.exists():
        log(f"Cleaning up temporary directory {output_dir}...", "🧹")
        shutil.rmtree(output_dir)
    
    log("Resume rendering and distribution complete!", "✅")

if __name__ == "__main__":
    render()
