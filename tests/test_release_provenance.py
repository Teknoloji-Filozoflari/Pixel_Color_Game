import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[1]
spec = importlib.util.spec_from_file_location("verify_runs", ROOT / "packaging/verify_release_runs.py")
verify_runs = importlib.util.module_from_spec(spec)
spec.loader.exec_module(verify_runs)


def successful_run():
    return dict(status="completed", conclusion="success", head_sha="current-commit",
                head_repository={"full_name": "owner/game"}, path=".github/workflows/windows.yml")


def test_successful_package_from_current_commit_is_accepted():
    verify_runs.validate_run(successful_run(), sha="current-commit", repository="owner/game",
                             workflow="windows.yml")


@pytest.mark.parametrize("change", [
    dict(head_sha="previous-release"),
    dict(head_repository={"full_name": "fork/game"}),
    dict(path=".github/workflows/python-package.yml"),
    dict(conclusion="failure"),
    dict(status="in_progress"),
])
def test_wrong_or_unverified_build_cannot_be_published(change):
    run = successful_run()
    run.update(change)
    with pytest.raises(ValueError, match="successful windows.yml run at commit current-commit"):
        verify_runs.validate_run(run, sha="current-commit", repository="owner/game", workflow="windows.yml")
