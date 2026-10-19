"""Read Adaptec controller inventory using arcconf (no shell or privileged actions)."""

import re
import subprocess
import time
from typing import Dict, List, Optional, Tuple

from ..config import Config

_FOOTER = re.compile(r"^Command completed successfully\.$", re.I)
_CONTROLLER = re.compile(r"^Controller\s+#?(\d+)(?:\s*:\s*(?::\s*)?.*)?$", re.I)
_FOUND = re.compile(r"^Controllers found\s*:\s*(\d+)$", re.I)
_LD = re.compile(r"^Logical Device number\s+(\d+)$", re.I)
_PD = re.compile(r"^Device\s+#(\d+)$", re.I)
_CHANNEL = re.compile(r"^(\d+)\s*,\s*(\d+)\s*\(\d+:\d+\)$")
_NUMBER = re.compile(r"^(\d+)\b")
_TEXT = re.compile(r"^[\w .+()/\-]{1,80}$", re.ASCII)
_SECTIONS = {
    "controller information": "ad",
    "logical device information": "ld",
    "physical device information": "pd",
}
_FIELDS = {
    "ad": {
        "controller status": "state",
        "controller mode": "mode",
        "controller model": "model",
        "temperature": "temperature",
        "defunct disk drive count": "defunct",
    },
    "ld": {"status of logical device": "state", "raid level": "raid_level"},
    "pd": {
        "state": "state",
        "model": "model",
        "reported channel,device(t:l)": "location",
        "current temperature": "temperature",
        "s.m.a.r.t.": "smart",
        "s.m.a.r.t. warnings": "warnings",
        "enclosure id": "enclosure",
        "type": "type",
    },
}


class ArcconfError(ValueError):
    """Command failed or inventory structurally incomplete."""


class ArcconfDeadlineExceeded(ArcconfError):
    """Total collection budget exhausted; no more commands may be started."""


def _lines(output: str) -> List[str]:
    lines = [line.strip() for line in output.splitlines()]
    while lines and not lines[-1]:
        lines.pop()
    if not any(_FOOTER.fullmatch(line) for line in lines):
        raise ArcconfError("arcconf output missing success footer")
    return lines


def parse_list(output: str) -> List[str]:
    """Require explicit IDs, validated count and successful completion."""
    lines = _lines(output)
    counts = [int(match.group(1)) for line in lines if (match := _FOUND.fullmatch(line))]
    ids = [match.group(1) for line in lines if (match := _CONTROLLER.fullmatch(line))]
    if not counts or len(set(counts)) != 1 or counts[0] != len(ids) or len(set(ids)) != len(ids):
        raise ArcconfError("invalid arcconf controller inventory")
    return ids


def parse_config(output: str, section: str) -> Tuple[Dict[str, str], List[Dict[str, str]]]:
    """Parse only allowlisted top-level fields within requested AD/LD/PD section."""
    lines = _lines(output)
    active = False
    seen_section = False
    nested = False
    current: Dict[str, str] = {}
    records: List[Dict[str, str]] = []
    seen_ids = set()

    def finish() -> None:
        if not current or section == "ad":
            return
        if section == "pd" and (
            "enclosure_device" in current
            or "enclosure" in current
            or current.get("type", "").lower()
            in {"ses", "ses2", "enclosure", "enclosure services device"}
        ):
            return
        if not current.get("state"):
            raise ArcconfError("arcconf device missing status")
        if section == "pd":
            location = _CHANNEL.fullmatch(current.get("location", ""))
            if not location:
                raise ArcconfError("arcconf physical device missing channel/device")
            current["channel_id"], current["device_id"] = location.groups()
            identity = (current["channel_id"], current["device_id"])
        else:
            identity = current["logical_drive_id"]
        if identity in seen_ids:
            raise ArcconfError("duplicate arcconf device identity")
        seen_ids.add(identity)
        records.append(current.copy())

    for line in lines:
        heading = _SECTIONS.get(line.lower())
        if heading:
            if active:
                finish()
                active = False
            if heading == section:
                if seen_section:
                    raise ArcconfError("duplicate arcconf section")
                seen_section = active = True
                current = {}
            continue
        if _FOOTER.fullmatch(line):
            if active:
                finish()
                active = False
            continue
        if not active:
            continue
        record = (_LD if section == "ld" else _PD).fullmatch(line)
        if section != "ad" and record:
            finish()
            current = {"logical_drive_id" if section == "ld" else "header_id": record.group(1)}
            nested = False
            continue
        if section == "pd" and re.fullmatch(r"Phy\s+#\d+", line, re.I):
            nested = True
            continue
        if section == "pd" and line.lower() == "device is an enclosure services device":
            current["enclosure_device"] = "true"
            continue
        if nested or (section != "ad" and not current):
            continue
        # Require whitespace before colon: values may contain colons (addresses, paths).
        field = re.match(r"^(.+?)\s+:\s*(.*)$", line)
        if field:
            key = _FIELDS[section].get(field.group(1).strip().lower())
            if key and key not in current:
                current[key] = field.group(2).strip()

    if not seen_section:
        raise ArcconfError("arcconf section missing")
    if section == "ad" and not current.get("state"):
        raise ArcconfError("arcconf controller missing status")
    return current, records


def safe_text(value: str) -> str:
    """Allow bounded, printable model/state labels; never export arbitrary CLI text."""
    return value if _TEXT.fullmatch(value) else "unknown"


def number(value: str):
    match = _NUMBER.match(value.strip())
    return int(match.group(1)) if match else None


class ArcConf:
    """Synchronous arcconf runner; subprocess.run kills and reaps timed-out children."""

    def __init__(self, config: Config) -> None:
        self.path = config.arcconf_path
        self.timeout = (
            config.collect_timeout if config.collect_timeout and config.collect_timeout > 0 else 30
        )

    def run(self, *args: str, deadline: Optional[float] = None) -> str:
        if args != ("LIST",) and (
            len(args) != 3
            or args[0] != "GETCONFIG"
            or not re.fullmatch(r"[0-9]+", args[1])
            or args[2] not in {"AD", "LD", "PD"}
        ):
            raise ArcconfError("invalid arcconf arguments")
        remaining = deadline - time.monotonic() if deadline is not None else float("inf")
        if remaining <= 0:
            raise ArcconfDeadlineExceeded("arcconf collection deadline exceeded")
        timeout = min(self.timeout, remaining)
        try:
            result = subprocess.run(
                [self.path, *args],
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                timeout=timeout,
                check=True,
                text=True,
                errors="replace",
            )
        except subprocess.TimeoutExpired as error:
            if remaining <= timeout or (deadline is not None and time.monotonic() >= deadline):
                raise ArcconfDeadlineExceeded("arcconf collection deadline exceeded") from error
            raise ArcconfError("arcconf command timed out") from error
        except (OSError, subprocess.SubprocessError, UnicodeDecodeError) as error:
            raise ArcconfError("arcconf execution failed") from error
        if deadline is not None and time.monotonic() >= deadline:
            raise ArcconfDeadlineExceeded("arcconf collection deadline exceeded")
        return result.stdout
