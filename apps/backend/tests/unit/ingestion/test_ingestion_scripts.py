from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).parents[5]
SCRIPT_RELATIVE_PATH = Path(
    "skills/vas-ifrs-document-ingestion/scripts/run_ingest.sh"
)


def _portable_project(tmp_path: Path) -> tuple[Path, Path]:
    project = tmp_path / "portable-project"
    script = project / SCRIPT_RELATIVE_PATH
    script.parent.mkdir(parents=True)
    shutil.copy2(PROJECT_ROOT / SCRIPT_RELATIVE_PATH, script)
    script.chmod(0o755)

    docs = project / "ingestion/raw/shared/vas/standards"
    docs.mkdir(parents=True)
    (docs / "vas-01.txt").write_text("Chuẩn mực chung", encoding="utf-8")
    return project, script


def test_run_ingest_is_portable_and_forwards_dry_run(tmp_path: Path) -> None:
    project, script = _portable_project(tmp_path)
    fake_python = tmp_path / "fake-python"
    capture = tmp_path / "python-args.txt"
    fake_python.write_text(
        '#!/usr/bin/env bash\nprintf "%s\\n" "$PWD" "$@" > "$INGEST_CAPTURE"\n',
        encoding="utf-8",
    )
    fake_python.chmod(0o755)
    env = {
        **os.environ,
        "INGEST_PYTHON": str(fake_python),
        "INGEST_CAPTURE": str(capture),
    }

    result = subprocess.run(
        [str(script), "--scope", "vas", "--dry-run"],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    invocation = capture.read_text(encoding="utf-8").splitlines()
    assert invocation[0] == str(project)
    assert "--dry-run" in invocation
    assert "--scope" in invocation
    assert "shared" in invocation


def test_run_ingest_rejects_invalid_tenant_id(tmp_path: Path) -> None:
    _project, script = _portable_project(tmp_path)

    result = subprocess.run(
        [str(script), "--scope", "tenant", "--tenant-id", "dev-tenant"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0
    assert "valid UUID" in result.stdout + result.stderr
