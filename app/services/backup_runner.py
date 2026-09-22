from pathlib import Path
import subprocess
import sys


def run_database_backup():
    """Run the existing database backup script and return its result."""

    project_root = Path(__file__).resolve().parents[2]
    script_path = project_root / "scripts" / "backup_db.py"

    result = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=str(project_root),
        capture_output=True,
        text=True,
    )

    return {
        "success": result.returncode == 0,
        "output": (result.stdout or "") + (result.stderr or ""),
    }
