from __future__ import annotations

import os
from pathlib import Path

from witnis.core.index import index_repository
from witnis.core.verify import run_verification

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "mini_py"


def test_run_verification_execute_pytest_on_fixture(tmp_path: Path) -> None:
    db = tmp_path / "index.sqlite"
    index_repository(FIXTURE, db, incremental=False)
    os.environ["WITNIS_ALLOW_VERIFY"] = "1"
    try:
        payload = run_verification(db, execute=True, target="login")
    finally:
        os.environ.pop("WITNIS_ALLOW_VERIFY", None)
    execution = payload["result"].get("execution") or []
    test_step = next(s for s in execution if s.get("step_id") == "run_tests")
    assert test_step.get("status") == "verified", test_step
    assert payload["result"]["state"] == "verified"


def test_run_verification_container_profile_on_fixture(tmp_path: Path) -> None:
    import subprocess

    import pytest

    from witnis.core.verify_isolate import detect_container_runtime

    runtime = detect_container_runtime()
    if runtime is None:
        pytest.skip("docker/podman daemon not running")
    image = os.environ.get("WITNIS_VERIFY_IMAGE")
    if not image:
        pytest.skip(
            "set WITNIS_VERIFY_IMAGE to an image that includes pytest "
            "(docker/verify.Dockerfile)"
        )
    probe = subprocess.run(
        [runtime, "image", "inspect", image],
        capture_output=True,
        timeout=30,
    )
    if probe.returncode != 0:
        pytest.skip(f"container image {image!r} is not present")
    db = tmp_path / "index.sqlite"
    index_repository(FIXTURE, db, incremental=False)
    prev_allow = os.environ.get("WITNIS_ALLOW_VERIFY")
    prev_image = os.environ.get("WITNIS_VERIFY_IMAGE")
    os.environ["WITNIS_ALLOW_VERIFY"] = "1"
    os.environ["WITNIS_VERIFY_IMAGE"] = image
    try:
        payload = run_verification(
            db, execute=True, target="login", profile="container"
        )
    finally:
        if prev_allow is None:
            os.environ.pop("WITNIS_ALLOW_VERIFY", None)
        else:
            os.environ["WITNIS_ALLOW_VERIFY"] = prev_allow
        if prev_image is None:
            os.environ.pop("WITNIS_VERIFY_IMAGE", None)
        else:
            os.environ["WITNIS_VERIFY_IMAGE"] = prev_image
    execution = payload["result"].get("execution") or []
    test_step = next(s for s in execution if s.get("step_id") == "run_tests")
    compile_step = next(s for s in execution if s.get("step_id") == "static_compile")
    assert compile_step.get("status") == "verified", compile_step
    assert test_step.get("status") == "verified", test_step
    iso = test_step.get("isolation") or {}
    assert iso.get("profile") == "container" or test_step.get("profile") == "container"
    assert payload["result"]["state"] == "verified"
