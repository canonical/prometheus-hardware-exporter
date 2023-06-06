"""Entrypoint for python package."""

from setuptools import setup

configs = {
    "name": "prometheus-hardware-exporter",
    "description": "exports hardware related metrics",
    "use_scm_version": True,
    "setup_requires": ["setuptools_scm", "pyyaml"],
    "author": "Canonical BootStack DevOps Centres",
    "packages": ["prometheus_hardware_exporter", "prometheus_hardware_exporter.collectors"],
    "url": "https://github.com/canonical/prometheus-hardware-exporter",
    "entry_points": {
        "console_scripts": [
            "prometheus-hardware-exporter=" + "prometheus_hardware_exporter.__main__:main",
        ]
    },
}

with open("requirements.txt", encoding="utf-8") as f:
    requirements = [req.strip() for req in f.readlines()]
    configs.update({"install_requires": requirements})

with open("LICENSE", encoding="utf-8") as f:
    configs.update({"license": f.read()})

with open("README.md", encoding="utf-8") as f:
    configs.update({"long_description": f.read()})


if __name__ == "__main__":
    setup(**configs)
