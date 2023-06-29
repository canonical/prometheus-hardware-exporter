#!/usr/bin/python3
"""Test prometheus-hardware-exporter package."""
from subprocess import run


def test_00_exporter_http_server_running(port):
    """Test if exporter is running."""
    result = run(f"curl http://localhost:{port}", shell=True, capture_output=True)
    assert result.returncode == 0
