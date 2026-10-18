"""Reject release artifacts built from a different commit or workflow."""

import json
import os
import subprocess

WORKFLOWS = {
    "APPIMAGE_RUN": "appimage.yml",
    "DEB_RUN": "debian-package.yml",
    "RPM_RUN": "rpm.yml",
    "SNAP_RUN": "snap.yml",
    "NIX_RUN": "nix.yml",
    "WINDOWS_RUN": "windows.yml",
}


def validate_run(run, *, sha, repository, workflow):
    if (run.get("status") != "completed" or run.get("conclusion") != "success"
            or run.get("head_sha") != sha
            or run.get("head_repository", {}).get("full_name") != repository
            or run.get("path", "").split("@")[0] != f".github/workflows/{workflow}"):
        raise ValueError(f"Release requires a successful {workflow} run at commit {sha}")


def main():
    repository, sha = os.environ["GITHUB_REPOSITORY"], os.environ["GITHUB_SHA"]
    for variable, workflow in WORKFLOWS.items():
        run_id = os.environ[variable]
        if not run_id.isascii() or not run_id.isdecimal():
            raise ValueError(f"Invalid run ID: {variable}")
        result = subprocess.run(["gh", "api", f"repos/{repository}/actions/runs/{run_id}"],
                                check=True, capture_output=True, text=True, encoding="utf-8")
        validate_run(json.loads(result.stdout), sha=sha, repository=repository, workflow=workflow)
        print(f"Verified {workflow}: {run_id} at {sha}")


if __name__ == "__main__":
    main()
