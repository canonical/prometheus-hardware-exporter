"""Sanitized arcconf 4.16 format and scrape failure behavior."""

import subprocess
import sys
import threading
from unittest.mock import Mock, patch

import pytest
from prometheus_client import CollectorRegistry, generate_latest

from prometheus_hardware_exporter import __main__
from prometheus_hardware_exporter.collector import AdaptecRAIDCollector
from prometheus_hardware_exporter.collectors.arcconf import (
    ArcConf,
    ArcconfDeadlineExceeded,
    ArcconfError,
    parse_config,
    parse_list,
)
from prometheus_hardware_exporter.config import Config

FOOTER = "Command completed successfully."
LIST = (
    f"Controllers found: 2\n"
    "Controller 1:             : Optimal, Slot 2, Mixed, Adaptec SmartHBA 2200-16i, REDACTED\n"
    "Controller 3:             : Optimal, Slot 3, Mixed, Adaptec SmartHBA 2200-16i, REDACTED\n"
    f"{FOOTER}"
)
AD = f"""Controllers found: 1
Controller information
Controller Status                          : Optimal
Controller Mode                            : Mixed
Controller Model                           : Adaptec SmartHBA 2200-16i
Temperature                                : 56 C/ 132 F (Normal)
Defunct disk drive count                   : 0
Controller Serial Number                   : SECRET
{FOOTER}"""
LD = f"""Logical device information
Logical Device number 0
Logical Device name                        : secret:mount
RAID level                                 : 5
Status of Logical Device                   : Optimal
Mount Points                               : /secret:path
{FOOTER}"""
PD = f"""Physical Device information
Device #0
State                                : Online
Reported Channel,Device(T:L)         : 0,0(0:0)
Model                                : Disk-Model
Serial number                        : SECRET
S.M.A.R.T.                           : No
S.M.A.R.T. warnings                  : 0
Current Temperature                  : 29 deg C
Phy #0
State                                : bogus nested PHY state
Device #0
State                                : Dedicated Hot-Spare
Reported Channel,Device(T:L)         : 1,0(0:0)
Model                                : Disk-Model
S.M.A.R.T.                           : Yes
Device #0
Reported Channel,Device(T:L)         : 2,0(0:0)
Device is an Enclosure Services Device
Type                                 : SAF-TE
Model                                : Virtual SGPIO
{FOOTER}"""


def samples(collector):
    return {
        sample.name: sample.value for family in collector.collect() for sample in family.samples
    }


def test_parse_real_format_and_nested_sections():
    assert parse_list(LIST) == ["1", "3"]
    ad, _ = parse_config(AD, "ad")
    assert ad["state"] == "Optimal"
    assert parse_config(LD, "ld")[1][0]["state"] == "Optimal"
    physical = parse_config(PD, "pd")[1]
    assert [(p["channel_id"], p["device_id"], p["state"]) for p in physical] == [
        ("0", "0", "Online"),
        ("1", "0", "Dedicated Hot-Spare"),
    ]
    assert "SECRET" not in str((ad, physical))


@pytest.mark.parametrize(
    "output",
    [
        "",
        "Controller 1: : Optimal, Slot 2\n" + FOOTER,
        "Controllers found: 0\nController 1: : Optimal, Slot 2\n" + FOOTER,
        "Controllers found: 2\nController 1: : Optimal\nController 1: : Optimal\n" + FOOTER,
    ],
)
def test_invalid_discovery(output):
    with pytest.raises(ArcconfError):
        parse_list(output)


def test_valid_empty_inventory():
    assert parse_list("Controllers found: 0\n" + FOOTER + "\n\n") == []


def test_duplicate_and_missing_section():
    with pytest.raises(ArcconfError):
        parse_config("Controller information\n" + AD, "ad")
    with pytest.raises(ArcconfError):
        parse_config(AD, "pd")
    assert (
        len(parse_config(LD.replace(FOOTER, "Physical Device information\n" + FOOTER), "ld")[1])
        == 1
    )


@pytest.mark.parametrize(
    "section,output",
    [
        ("ad", "Controller information\nController Model : X\n" + FOOTER),
        ("ld", "Logical device information\nLogical Device number 0\n" + FOOTER),
        (
            "ld",
            LD.replace(
                "Logical Device number 0",
                "Logical Device number 0\nStatus of Logical Device : Optimal\nLogical Device number 0",
            ),
        ),
        ("pd", PD.replace("1,0(0:0)", "0,0(0:0)")),
        ("pd", PD.replace("1,0(0:0)", "invalid")),
        ("pd", PD.replace("State                                : Online\n", "", 1)),
        ("pd", PD.replace(FOOTER, "")),
    ],
)
def test_malformed_sections(section, output):
    with pytest.raises(ArcconfError):
        parse_config(output, section)


def test_controller_atomic_publication_and_exposition():
    collector = AdaptecRAIDCollector(Config())
    collector.arcconf.run = Mock(side_effect=[LIST, AD, LD, PD, AD, LD, "broken"])
    registry = CollectorRegistry()
    registry.register(collector)
    assert collector.arcconf.run.call_count == 0
    text = generate_latest(registry).decode()
    assert collector.arcconf.run.call_args_list[0].args == ("LIST",)
    assert "arcconf_command_success 0.0" in text
    assert 'arcconf_command_ctrl_success{controller_id="1"} 1.0' in text
    assert 'arcconf_command_ctrl_success{controller_id="3"} 0.0' in text
    assert 'adaptec_physical_drives{controller_id="1"} 2.0' in text
    assert (
        'adaptec_physical_drive_smart_alert{channel_id="1",controller_id="1",device_id="0"} 1.0'
        in text
    )
    assert "SECRET" not in text and "secret:mount" not in text
    assert text.count("# HELP adaptec_physical_drive_healthy ") == 1
    assert text.count("# TYPE adaptec_physical_drive_healthy ") == 1
    collector.arcconf.run = Mock(return_value="invalid")
    assert samples(collector) == {
        "arcconf_command_success": 0,
        "arcconf_collection_incomplete": 1,
        "arcconf_collection_deadline_exceeded": 0,
    }


def test_degraded_unknown_optional_and_zero():
    collector = AdaptecRAIDCollector(Config())
    collector.arcconf.run = Mock(
        side_effect=[
            "Controllers found: 1\nController #1\n" + FOOTER,
            AD.replace("Optimal", "Degraded").replace("56 C/ 132 F (Normal)", "N/A"),
            LD.replace("Optimal", "Unknown"),
            PD.replace("Online", "Failed")
            .replace("29 deg C", "Unavailable")
            .replace(
                "S.M.A.R.T.                           : No",
                "S.M.A.R.T.                           : Unknown",
            ),
        ]
    )
    families = list(collector.collect())
    values = {sample.name: sample.value for family in families for sample in family.samples}
    assert values["arcconf_command_success"] == 1
    assert values["adaptec_controller_healthy"] == 0
    assert values["adaptec_logical_drive_healthy"] == 0
    assert sorted(
        sample.value
        for family in families
        for sample in family.samples
        if sample.name == "adaptec_physical_drive_healthy"
    ) == [0, 1]
    assert "adaptec_controller_temperature_celsius" not in values
    assert "adaptec_physical_drive_temperature_celsius" not in values


def test_cli_config_default_off_and_registration(monkeypatch):
    monkeypatch.setattr("sys.argv", ["exporter", "--collector.adaptec_raid"])
    assert vars(__main__.parse_command_line())["collector.adaptec_raid"] is True
    assert Config().enable_collectors == []
    assert Config(enable_collectors=["collector.adaptec_raid"]).enable_collectors
    assert isinstance(
        __main__.get_collector_registries(Config())["collector.adaptec_raid"], AdaptecRAIDCollector
    )


def test_runner_argv_timeout_and_validation():
    runner = ArcConf(Config(collect_timeout=2))
    with patch("subprocess.run", return_value=Mock(stdout=LIST)) as run:
        assert runner.run("LIST") == LIST
        runner.run("GETCONFIG", "1", "AD")
        assert run.call_args.args[0] == ["/usr/sbin/arcconf", "GETCONFIG", "1", "AD"]
        assert run.call_args.kwargs["timeout"] == 2
    with pytest.raises(ArcconfError):
        runner.run("GETCONFIG", "1;id", "AD")
    with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("arcconf", 2)):
        with pytest.raises(ArcconfError):
            runner.run("LIST")


def test_overlapping_scrapes_return_failure_without_running_second_scan():
    collector = AdaptecRAIDCollector(Config())
    entered, release = threading.Event(), threading.Event()

    def slow_run(*args, **kwargs):
        entered.set()
        release.wait(2)
        return "Controllers found: 0\n" + FOOTER

    collector.arcconf.run = Mock(side_effect=slow_run)
    worker = threading.Thread(target=lambda: samples(collector))
    worker.start()
    try:
        assert entered.wait(2)
        assert samples(collector) == {
            "arcconf_command_success": 0,
            "arcconf_collection_incomplete": 1,
            "arcconf_collection_deadline_exceeded": 0,
        }
        assert collector.arcconf.run.call_count == 1
    finally:
        release.set()
        worker.join(2)


def test_unexpected_scan_exception_returns_failure():
    collector = AdaptecRAIDCollector(Config())
    collector.arcconf.run = Mock(side_effect=RuntimeError("internal error"))
    assert samples(collector) == {
        "arcconf_command_success": 0,
        "arcconf_collection_incomplete": 1,
        "arcconf_collection_deadline_exceeded": 0,
    }


def test_process_passthrough():
    collector = AdaptecRAIDCollector(Config())
    assert collector.process([], {}) == []


def test_runner_explicit_path_and_deadline_timeout():
    runner = ArcConf(Config(arcconf_path="/opt/adaptec/arcconf", collect_timeout=30))
    with patch("prometheus_hardware_exporter.collectors.arcconf.time.monotonic", return_value=10):
        with patch("subprocess.run", return_value=Mock(stdout=LIST)) as run:
            assert runner.run("LIST", deadline=12) == LIST
            assert run.call_args.args[0] == ["/opt/adaptec/arcconf", "LIST"]
            assert run.call_args.kwargs["timeout"] == 2
            assert not run.call_args.kwargs.get("shell", False)
        with patch("subprocess.run") as run:
            with pytest.raises(ArcconfDeadlineExceeded):
                runner.run("LIST", deadline=10)
            run.assert_not_called()
        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("arcconf", 2)):
            with pytest.raises(ArcconfDeadlineExceeded):
                runner.run("LIST", deadline=12)
        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("arcconf", 30)):
            with pytest.raises(ArcconfError) as error:
                runner.run("LIST", deadline=100)
            assert not isinstance(error.value, ArcconfDeadlineExceeded)


def test_runner_rejects_result_after_deadline():
    runner = ArcConf(Config())
    with patch(
        "prometheus_hardware_exporter.collectors.arcconf.time.monotonic", side_effect=[0, 2]
    ):
        with patch("subprocess.run", return_value=Mock(stdout=LIST)):
            with pytest.raises(ArcconfDeadlineExceeded):
                runner.run("LIST", deadline=2)


@pytest.mark.parametrize("now", [12, 12.1])
def test_runner_timeout_overrun_exhausts_deadline(now):
    runner = ArcConf(Config(collect_timeout=2))
    timeout_error = subprocess.TimeoutExpired("arcconf", 2)
    with patch(
        "prometheus_hardware_exporter.collectors.arcconf.time.monotonic",
        side_effect=[9.9, now],
    ):
        with patch("subprocess.run", side_effect=timeout_error) as command:
            with pytest.raises(ArcconfDeadlineExceeded) as error:
                runner.run("LIST", deadline=12)
    assert command.call_args.kwargs["timeout"] == 2
    assert error.value.__cause__ is timeout_error


@pytest.mark.parametrize(
    "execution_error",
    [
        OSError("cannot execute arcconf"),
        subprocess.CalledProcessError(1, "arcconf"),
        UnicodeDecodeError("utf-8", b"\xff", 0, 1, "invalid byte"),
    ],
)
def test_runner_execution_failure_maps_error_and_emits_metrics(execution_error):
    collector = AdaptecRAIDCollector(Config())
    with patch("subprocess.run", side_effect=execution_error):
        with pytest.raises(ArcconfError) as error:
            collector.arcconf.run("LIST")
        assert error.value.__cause__ is execution_error
        assert samples(collector) == {
            "arcconf_command_success": 0,
            "arcconf_collection_incomplete": 1,
            "arcconf_collection_deadline_exceeded": 0,
        }
    assert not collector._scan_lock.locked()


def test_runner_replaces_invalid_output_bytes():
    runner = ArcConf(Config())
    subprocess_run = subprocess.run

    def emit_invalid_bytes(*args, **kwargs):
        return subprocess_run(
            [
                sys.executable,
                "-c",
                "import sys; sys.stdout.buffer.write("
                "b'Invalid byte: \\xff\\nControllers found: 0\\n"
                "Command completed successfully.\\n')",
            ],
            **kwargs,
        )

    with patch("subprocess.run", side_effect=emit_invalid_bytes) as command:
        output = runner.run("LIST")
    assert command.call_args.kwargs["errors"] == "replace"
    assert "\ufffd" in output
    assert parse_list(output) == []


def test_timeout_overrun_stops_collection_and_emits_deadline_metric():
    collector = AdaptecRAIDCollector(Config(collection_timeout=2.1, collect_timeout=2))
    now = [0.0]

    def run(*args, **kwargs):
        if args[0][-1] == "LIST":
            return Mock(stdout=LIST)
        now[0] = 2.1
        raise subprocess.TimeoutExpired(args[0], kwargs["timeout"])

    with patch(
        "prometheus_hardware_exporter.collectors.arcconf.time.monotonic",
        side_effect=lambda: now[0],
    ):
        with patch("subprocess.run", side_effect=run) as command:
            values = samples(collector)
    assert command.call_count == 2
    assert values["arcconf_command_success"] == 0
    assert values["arcconf_collection_incomplete"] == 1
    assert values["arcconf_collection_deadline_exceeded"] == 1
    assert not collector._scan_lock.locked()


def test_controller_results_crossing_deadline_are_not_published():
    collector = AdaptecRAIDCollector(Config(collection_timeout=2))
    collector.arcconf.run = Mock(return_value=LIST)
    with patch(
        "prometheus_hardware_exporter.collector.time.monotonic",
        side_effect=[0, 0, 2],
    ):
        with patch.object(collector, "_controller_payloads", return_value=[]) as scan:
            values = samples(collector)
    scan.assert_called_once_with("1", 2)
    collector.arcconf.run.assert_called_once_with("LIST", deadline=2)
    assert values["arcconf_command_success"] == 0
    assert values["arcconf_collection_incomplete"] == 1
    assert values["arcconf_collection_deadline_exceeded"] == 1
    assert values["arcconf_command_ctrl_success"] == 0
    assert "adaptec_physical_drives" not in values
    assert not collector._scan_lock.locked()


def test_total_deadline_keeps_completed_controller_and_stops_commands():
    collector = AdaptecRAIDCollector(Config(collection_timeout=5, collect_timeout=30))
    now = [0.0]
    outputs = iter(
        [
            LIST.replace("Controllers found: 2", "Controllers found: 3").replace(
                FOOTER, "Controller #5\n" + FOOTER
            ),
            AD,
            LD,
            PD,
        ]
    )
    timeouts = []

    def run(*args, **kwargs):
        timeouts.append(kwargs["timeout"])
        if len(timeouts) == 5:
            now[0] += kwargs["timeout"]
            raise subprocess.TimeoutExpired(args[0], kwargs["timeout"])
        now[0] += 1
        return Mock(stdout=next(outputs))

    with patch(
        "prometheus_hardware_exporter.collectors.arcconf.time.monotonic",
        side_effect=lambda: now[0],
    ):
        with patch("subprocess.run", side_effect=run) as command:
            registry = CollectorRegistry()
            registry.register(collector)
            text = generate_latest(registry).decode()
            assert command.call_count == 5
    assert timeouts == [5, 4, 3, 2, 1]
    assert now[0] == 5
    assert "arcconf_command_success 0.0" in text
    assert "arcconf_collection_incomplete 1.0" in text
    assert "arcconf_collection_deadline_exceeded 1.0" in text
    assert 'arcconf_command_ctrl_success{controller_id="1"} 1.0' in text
    assert 'arcconf_command_ctrl_success{controller_id="3"} 0.0' in text
    assert 'arcconf_command_ctrl_success{controller_id="5"} 0.0' in text
    assert 'adaptec_physical_drives{controller_id="1"} 2.0' in text
    assert 'adaptec_physical_drives{controller_id="3"}' not in text
    assert not collector._scan_lock.locked()


def test_discovery_deadline_reports_incomplete():
    collector = AdaptecRAIDCollector(Config())
    collector.arcconf.run = Mock(side_effect=ArcconfDeadlineExceeded("deadline"))
    assert samples(collector) == {
        "arcconf_command_success": 0,
        "arcconf_collection_incomplete": 1,
        "arcconf_collection_deadline_exceeded": 1,
    }
    collector.arcconf.run = Mock(return_value="Controllers found: 0\n" + FOOTER)
    assert samples(collector) == {
        "arcconf_command_success": 1,
        "arcconf_collection_incomplete": 0,
        "arcconf_collection_deadline_exceeded": 0,
        "adaptec_controllers": 0,
    }


def test_per_command_timeout_keeps_previous_metrics_and_continues():
    collector = AdaptecRAIDCollector(Config(collect_timeout=1))
    with patch(
        "subprocess.run",
        side_effect=[
            Mock(stdout=LIST),
            subprocess.TimeoutExpired("arcconf", 1),
            Mock(stdout=AD),
            Mock(stdout=LD),
            Mock(stdout=PD),
        ],
    ) as command:
        registry = CollectorRegistry()
        registry.register(collector)
        text = generate_latest(registry).decode()
        assert command.call_count == 5
        assert all(call.kwargs["timeout"] == 1 for call in command.call_args_list)
    assert "arcconf_collection_incomplete 1.0" in text
    assert "arcconf_collection_deadline_exceeded 0.0" in text
    assert 'arcconf_command_ctrl_success{controller_id="1"} 0.0' in text
    assert 'arcconf_command_ctrl_success{controller_id="3"} 1.0' in text
    assert 'adaptec_physical_drives{controller_id="3"} 2.0' in text
