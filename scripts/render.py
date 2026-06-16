from ruamel.yaml import YAML
import copy
import json
import shutil
from pathlib import Path
import subprocess
import sys

def log(message, symbol="ℹ️"):
    print(f"{symbol} {message}")

LANGUAGES = {
    "en": {
        "locale_file": Path("locales/en.json"),
        "rendercv_language": "english",
        "pdf": Path("dist/Torben-Haack.pdf"),
        "markdown": Path("README.md"),
    },
    "de": {
        "locale_file": Path("locales/de.json"),
        "rendercv_language": "german",
        "pdf": Path("dist/Torben-Haack-de.pdf"),
        "markdown": Path("dist/README.de.md"),
    },
}


def load_json(path):
    if not path.exists():
        log(f"Error: {path} not found.", "❌")
        sys.exit(1)

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def lookup_locale_value(locale, key):
    current = locale
    for part in key.split("."):
        if not isinstance(current, dict) or part not in current:
            raise KeyError(key)
        current = current[part]
    return copy.deepcopy(current)


def resolve_i18n(value, locale):
    if isinstance(value, str) and value.startswith("i18n."):
        return lookup_locale_value(locale, value.removeprefix("i18n."))

    if isinstance(value, list):
        return [resolve_i18n(item, locale) for item in value]

    if isinstance(value, dict):
        return {key: resolve_i18n(item, locale) for key, item in value.items()}

    return value


def render_language(language_code, config, template_data, yaml, output_dir):
    locale = load_json(config["locale_file"])
    data = resolve_i18n(copy.deepcopy(template_data), locale)
    data["locale"]["language"] = config["rendercv_language"]

    language_dir = output_dir / language_code
    language_dir.mkdir(parents=True, exist_ok=True)
    resolved_cv_path = language_dir / "cv.yaml"
    with open(resolved_cv_path, "w", encoding="utf-8") as f:
        yaml.dump(data, f)

    name = data["cv"]["name"]
    safe_name = name.replace(" ", "_")

    log(f"Rendering {language_code.upper()} CV for {name} using RenderCV...", "🚀")
    try:
        subprocess.run(["rendercv", "render", "cv.yaml"], check=True, cwd=language_dir)
    except subprocess.CalledProcessError as e:
        log(f"RenderCV failed for {language_code.upper()} with error: {e}", "❌")
        sys.exit(1)
    except FileNotFoundError:
        log("RenderCV executable not found. Run this script through the project environment, for example: uv run scripts/render.py", "❌")
        sys.exit(1)

    mapping = {
        f"{safe_name}_CV.pdf": config["pdf"],
        f"{safe_name}_CV.md": config["markdown"],
    }

    for src_name, dest_path in mapping.items():
        src_path = next(language_dir.rglob(src_name), None)
        if src_path:
            log(f"Copying {src_path} to {dest_path}...", "📦")
            shutil.copy2(src_path, dest_path)
        else:
            log(f"Warning: Could not find {src_name} in {language_dir}", "⚠️")


def render():
    cv_path = Path("cv.yaml")
    if not cv_path.exists():
        log(f"Error: {cv_path} not found.", "❌")
        sys.exit(1)

    yaml = YAML(typ='safe')
    yaml.default_flow_style = False

    log(f"Loading CV template from {cv_path}...")
    with open(cv_path, "r", encoding="utf-8") as f:
        template_data = yaml.load(f)

    output_dir = Path("rendercv_output")
    dist_dir = Path("dist")

    log(f"Ensuring distribution directory {dist_dir} exists...", "📂")
    dist_dir.mkdir(parents=True, exist_ok=True)
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    for language_code, config in LANGUAGES.items():
        try:
            render_language(language_code, config, template_data, yaml, output_dir)
        except KeyError as e:
            log(f"Missing locale key for {language_code.upper()}: {e.args[0]}", "❌")
            sys.exit(1)

    if output_dir.exists():
        log(f"Cleaning up temporary directory {output_dir}...", "🧹")
        shutil.rmtree(output_dir)
    
    log("CV rendering and distribution complete!", "✅")

if __name__ == "__main__":
    render()
