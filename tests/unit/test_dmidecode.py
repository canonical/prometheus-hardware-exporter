import unittest
from unittest.mock import patch

from prometheus_hardware_exporter.collectors.dmidecode import Dmidecode
from prometheus_hardware_exporter.config import Config
from prometheus_hardware_exporter.utils import Command, Result

TYPE_39_OUTPUT = "tests/unit/test_resources/dmidecode/dmidecode_type_39_output.txt"


class TestDmidecode(unittest.TestCase):
    """Test the Dmidecode class."""

    @patch.object(Command, "__call__")
    def test_00_get_power_capacities_success(self, mock_call):
        with open(TYPE_39_OUTPUT, "r") as content:
            mock_call.return_value = Result(content.read(), None)
        config = Config()
        dmidecode = Dmidecode(config)
        power_capacities = dmidecode.get_power_capacities()
        self.assertEqual(power_capacities, [1400, 1400])

    @patch.object(Command, "__call__")
    def test_01_get_power_capacities_error(self, mock_call):
        mock_call.return_value = Result("", True)

        config = Config()
        dmidecode = Dmidecode(config)
        power_capacities = dmidecode.get_power_capacities()
        self.assertEqual(power_capacities, [])
