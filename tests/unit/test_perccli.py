import json
from unittest.mock import Mock, patch

import pytest

from prometheus_hardware_exporter.collectors.perccli import PercCLI
from prometheus_hardware_exporter.utils import Command, Result

PERCCLI_NO_CONTROLLER = "tests/unit/test_resources/perccli/perccli_not_controller.json"
PERCCLI_OUTPUT = "tests/unit/test_resources/perccli/perccli_output.json"


@pytest.fixture
def mock_get_ctrl_no_controller():
    with open(PERCCLI_NO_CONTROLLER, "r") as content:
        return_json = json.loads(content.read())
    with patch.object(
        PercCLI,
        "_get_controllers",
        return_value=return_json,
    ) as mock_get_ctrl:
        yield mock_get_ctrl


@pytest.fixture
def mock_get_ctrl_error():
    with patch.object(
        PercCLI, "_get_controllers", return_value=ValueError("get_ctrl_err_for_test")
    ) as mock_get_ctrl:
        yield mock_get_ctrl


@pytest.fixture
def mock_get_ctrl():
    with open(PERCCLI_OUTPUT, "r") as content:
        return_json = json.loads(content.read())
    with patch.object(
        PercCLI,
        "_get_controllers",
        return_value=return_json,
    ) as mock_get_ctrl:
        yield mock_get_ctrl


class TestPercCLI:
    def test_00_no_controller(self, mock_get_ctrl_no_controller):
        """Command success but not controller exists."""
        cli = PercCLI()
        assert cli.ctrl_successes() == {}
        assert cli.success() is True
        assert cli.ctrl_exists() is False

    def test_01_no_success(self, mock_get_ctrl_error):
        """Command success but not controller exists."""
        cli = PercCLI()
        assert cli.success() is False

    def test_02_get_controllers(self, mock_get_ctrl):
        cli = PercCLI()
        assert cli.get_controllers() == {"count": 1}

    def test_03_get_controllers_error(self, mock_get_ctrl_error):
        cli = PercCLI()
        assert cli.ctrl_exists() is False
        assert cli.ctrl_successes() == {}
        assert cli.get_controllers() == {}

    def test_04_get_virtual_drives(self, mock_get_ctrl):
        cli = PercCLI()
        assert cli.get_virtual_drives() == {
            0: [{"DG": "0", "VD": "0", "cache": "NRWTD", "state": "Optl"}]
        }

    def test_05_get_virtual_drives_error(self, mock_get_ctrl_error):
        cli = PercCLI()
        assert cli.get_virtual_drives() == {}

    def test_06_cmd_status(self, mock_get_ctrl):
        cli = PercCLI()
        result = cli._get_controllers()

        for controller in result["Controllers"]:
            cmd_status = cli._cmd_status(controller)
            assert cmd_status is True

    def test_07_cmd_status_fail(self, mock_get_ctrl_no_controller):
        cli = PercCLI()
        result = cli._get_controllers()

        for controller in result["Controllers"]:
            cmd_status = cli._cmd_status(controller)
            assert cmd_status is False

    @patch.object(Command, "__call__")
    def test_08__get_controllers(self, mock_call):
        with open(PERCCLI_OUTPUT, "r") as content:
            return_data = content.read()
        mock_call.return_value = Result(data=return_data)
        cli = PercCLI()
        result = cli._get_controllers()
        assert not isinstance(result, Exception)

    @patch.object(Command, "__call__")
    def test_09__get_controllers_fail(self, mock_call):
        err_mock = Mock()
        mock_call.return_value = Result(data=None, error=err_mock)
        cli = PercCLI()
        result = cli._get_controllers()
        assert result == err_mock

    @patch.object(Command, "__call__")
    @patch("prometheus_hardware_exporter.collectors.perccli.get_json_output")
    def test_10__get_controllers_get_json_output_fail(
        self,
        mock_get_json_output,
        mock_call,
    ):
        mock_call.return_value = Result()
        err_mock = Mock()
        mock_get_json_output.return_value = Result(data=None, error=err_mock)
        cli = PercCLI()
        result = cli._get_controllers()
        assert result.error == err_mock

    def test_11_ctrl_successes(self, mock_get_ctrl):
        cli = PercCLI()
        assert cli.ctrl_successes() == {0: True}
        assert cli.ctrl_exists() is True
        assert cli.success() is True

    def test_12_get_physical_devices(self, mock_get_ctrl):
        cli = PercCLI()
        assert cli.ctrl_successes() == {0: True}
        assert cli.ctrl_exists() is True

        assert cli.get_physical_devices() == {
            0: [
                {
                    "eid": "69",
                    "slt": "0",
                    "state": "Onln",
                    "DG": 0,
                    "size": "558.375 GB",
                    "media_type": "HDD",
                },
                {
                    "eid": "69",
                    "slt": "1",
                    "state": "Onln",
                    "DG": 0,
                    "size": "558.375 GB",
                    "media_type": "HDD",
                },
            ]
        }

    def test_13_get_physical_devices_error(self, mock_get_ctrl_error):
        cli = PercCLI()
        assert cli.get_physical_devices() == {}
