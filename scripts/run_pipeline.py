"""Run the complete analysis pipeline without opening JupyterLab."""

from pathlib import Path
import subprocess
import sys

import nbformat
from nbclient import NotebookClient


ROOT = Path(__file__).resolve().parents[1]
NOTEBOOKS = sorted((ROOT / "notebooks").glob("*.ipynb"))


def main() -> None:
    for old in (ROOT / "visualizations").rglob("*.png"):
        old.unlink()  # avoid stale charts from earlier runs
    if not NOTEBOOKS:
        raise SystemExit("No notebooks found.")

    for path in NOTEBOOKS:
        print(f"\nRunning {path.name} ...", flush=True)
        notebook = nbformat.read(path, as_version=4)
        NotebookClient(notebook, timeout=300, kernel_name="python3").execute(cwd=str(path.parent))
        nbformat.write(notebook, path)  # keep fresh outputs in the committed notebooks
        print(f"PASS: {path.name}", flush=True)

    print("\nGenerating visualization catalog ...", flush=True)
    subprocess.run([sys.executable, str(ROOT / "scripts" / "generate_visualizations.py")], cwd=ROOT, check=True)

    print("\nRunning SQL queries (DuckDB) ...", flush=True)
    subprocess.run([sys.executable, str(ROOT / "scripts" / "run_sql.py")], cwd=ROOT, check=True)

    print("\nBuilding dashboard data ...", flush=True)
    subprocess.run([sys.executable, str(ROOT / "scripts" / "build_dashboard_data.py")], cwd=ROOT, check=True)

    print("\nGenerating business report from processed outputs ...", flush=True)
    subprocess.run([sys.executable, str(ROOT / "scripts" / "generate_report.py")], cwd=ROOT, check=True)

    print("\nRunning final QA ...", flush=True)
    subprocess.run([sys.executable, str(ROOT / "scripts" / "validate_project.py")], cwd=ROOT, check=True)
    print("\nComplete pipeline finished successfully.")


if __name__ == "__main__":
    main()
