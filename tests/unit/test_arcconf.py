"""Arcconf fixtures exercised through the validated runner and parser."""

import subprocess
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from prometheus_hardware_exporter.collector import AdaptecRAIDCollector
from prometheus_hardware_exporter.collectors.arcconf import (
    ArcConf,
    ArcconfError,
    parse_config,
    parse_list,
)
from prometheus_hardware_exporter.config import Config

RESOURCES = Path(__file__).parent / "test_resources" / "arcconf"
# Original fixtures predate validation of arcconf's successful-completion footer.
LIST_OUTPUT = (RESOURCES / "list_output.txt").read_text() + "\nCommand completed successfully."
GETCONFIG_OUTPUT = (
    RESOURCES / "getconfig_al.txt"
).read_text() + "\nCommand completed successfully."


class TestArcConf(unittest.TestCase):
    @patch("subprocess.run")
    def test_list_controllers_okay(self, mock_run):
        mock_run.return_value = Mock(stdout=LIST_OUTPUT)
        self.assertEqual(parse_list(ArcConf(Config()).run("LIST")), ["1"])
        self.assertTrue(mock_run.call_args.kwargs["check"])

    @patch("subprocess.run")
    def test_list_controllers_fail(self, mock_run):
        mock_run.side_effect = subprocess.CalledProcessError(1, "arcconf", output=LIST_OUTPUT)
        with self.assertRaises(ArcconfError):
            ArcConf(Config()).run("LIST")

    def test_parse_with_leading_and_trailing_warnings(self):
        warning = "Could not open log file: /var/log/UcliEvt.log"
        for leading, trailing in [(True, False), (False, True), (True, True)]:
            prefix = warning + "\n" if leading else ""
            suffix = "\n" + warning if trailing else ""
            with self.subTest(command="LIST", leading=leading, trailing=trailing):
                self.assertEqual(parse_list(prefix + LIST_OUTPUT + suffix), ["1"])
            for section in ["ad", "ld", "pd"]:
                with self.subTest(section=section, leading=leading, trailing=trailing):
                    self.assertEqual(
                        parse_config(prefix + GETCONFIG_OUTPUT + suffix, section),
                        parse_config(GETCONFIG_OUTPUT, section),
                    )

    def test_missing_or_near_match_success_rejected(self):
        footer = "Command completed successfully."
        for success in ["", footer[:-1], footer + " warning", "prefix " + footer]:
            with self.subTest(command="LIST", success=success):
                with self.assertRaisesRegex(ArcconfError, "missing success footer"):
                    parse_list(LIST_OUTPUT.replace(footer, success))
            for section in ["ad", "ld", "pd"]:
                with self.subTest(section=section, success=success):
                    with self.assertRaisesRegex(ArcconfError, "missing success footer"):
                        parse_config(GETCONFIG_OUTPUT.replace(footer, success), section)

    def test_success_matching_ignores_case_and_whitespace(self):
        footer = "Command completed successfully."
        success = " \t" + footer.upper() + " \t\nwarning"
        self.assertEqual(parse_list(LIST_OUTPUT.replace(footer, success)), ["1"])
        for section in ["ad", "ld", "pd"]:
            with self.subTest(section=section):
                self.assertEqual(
                    parse_config(GETCONFIG_OUTPUT.replace(footer, success), section),
                    parse_config(GETCONFIG_OUTPUT, section),
                )

    @patch("subprocess.run")
    def test_get_all_information_okay(self, mock_run):
        mock_run.side_effect = [
            Mock(stdout=LIST_OUTPUT),
            Mock(stdout=GETCONFIG_OUTPUT),
            Mock(stdout=GETCONFIG_OUTPUT),
            Mock(stdout=GETCONFIG_OUTPUT),
        ]
        collector = AdaptecRAIDCollector(Config())
        payloads = collector.fetch()
        values = {payload.name: payload.value for payload in payloads}
        self.assertEqual(values["arcconf_command_success"], 1)
        self.assertEqual(values["adaptec_controllers"], 1)
        self.assertEqual(values["adaptec_logical_drives"], 2)
        self.assertEqual(values["adaptec_ready_logical_drives"], 1)
        self.assertEqual(values["adaptec_unready_logical_drives"], 1)
        self.assertEqual(values["adaptec_physical_drives"], 3)
        self.assertEqual(
            [call.args[0] for call in mock_run.call_args_list],
            [
                ["/usr/sbin/arcconf", "LIST"],
                ["/usr/sbin/arcconf", "GETCONFIG", "1", "AD"],
                ["/usr/sbin/arcconf", "GETCONFIG", "1", "LD"],
                ["/usr/sbin/arcconf", "GETCONFIG", "1", "PD"],
            ],
        )
        self.assertNotIn("RAID10-Data", str(payloads))
        self.assertNotIn("SERIAL-REDACTED", str(payloads))

    @patch("subprocess.run")
    def test_get_all_information_fail(self, mock_run):
        mock_run.side_effect = subprocess.CalledProcessError(1, "arcconf")
        payloads = AdaptecRAIDCollector(Config()).fetch()
        self.assertEqual(
            {payload.name: payload.value for payload in payloads},
            {
                "arcconf_command_success": 0,
                "arcconf_collection_incomplete": 1,
                "arcconf_collection_deadline_exceeded": 0,
            },
        )

    def test_parse_logical_drives(self):
        logical = parse_config(GETCONFIG_OUTPUT, "ld")[1]
        self.assertEqual(
            logical,
            [
                {"logical_drive_id": "0", "state": "Optimal", "raid_level": "10"},
                {"logical_drive_id": "1", "state": "Degraded", "raid_level": "5"},
            ],
        )

    def test_parse_physical_drives(self):
        physical = parse_config(GETCONFIG_OUTPUT, "pd")[1]
        self.assertEqual(
            physical,
            [
                {
                    "header_id": str(index),
                    "state": state,
                    "location": f"0,{index}(0:{index})",
                    "model": "ST600MP0006",
                    "channel_id": "0",
                    "device_id": str(index),
                }
                for index, state in enumerate(["Online", "Online", "Ready"])
            ],
        )
