from __future__ import annotations

import pytest

from app.workers.gl_tasks import process_gl_upload
from app.workers.report_tasks import generate_report_task


def test_unimplemented_workers_do_not_report_done() -> None:
    with pytest.raises(NotImplementedError):
        process_gl_upload.run("upload-1")

    with pytest.raises(NotImplementedError):
        generate_report_task.run("report-1", "balance_sheet", "2026-06")
