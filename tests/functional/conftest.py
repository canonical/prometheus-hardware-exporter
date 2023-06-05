import logging
import os
import time
from subprocess import check_call

import pytest

TMP_DIR = "/tmp"
SETUP_TIMEOUT = 5


@pytest.fixture(scope="session")
def snap_name():
    return "prometheus-hardware-exporter"


@pytest.fixture(scope="session")
def snap_config(snap_name):
    return f"/var/snap/{snap_name}/current/config.yaml"


@pytest.fixture(scope="session", autouse=True)
def setup_snap(snap_name):
    """Install the package to the system and cleanup afterwards.

    Note: an environment variable TEST_SNAP is needed to install the snap.
    """
    test_snap = os.environ.get("TEST_SNAP", None)
    if test_snap:
        logging.info("Installing %s snap package...", test_snap)
        assert os.path.isfile(test_snap)
        assert check_call(f"sudo snap install --dangerous --classic {test_snap}".split()) == 0
        assert check_call(f"sudo snap start {snap_name}".split()) == 0
    else:
        logging.error(
            "Could not find %s snap package for testing. Needs to build it first.",
            snap_name,
        )

    down = 1
    stime = time.time()
    while time.time() - stime < SETUP_TIMEOUT and down:
        try:
            down = check_call("curl http://localhost:10000".split())
        except Exception:
            time.sleep(0.5)
    assert not down, "Snap is not up."

    yield test_snap

    if test_snap:
        logging.info("Removing %s snap package...", snap_name)
        check_call(f"sudo snap remove {snap_name}".split())
