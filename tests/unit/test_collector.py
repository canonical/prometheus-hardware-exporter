import unittest
from unittest.mock import Mock, patch

from redfish.rest.v1 import (
    InvalidCredentialsError,
    RetriesExhaustedError,
    SessionCreationError,
)
from test_resources.ipmi.ipmi_sample_data import (
    SAMPLE_IPMI_SEL_ENTRIES,
    SAMPLE_IPMI_SENSOR_ENTRIES,
)

from prometheus_hardware_exporter.collector import (
    IpmiDcmiCollector,
    IpmiSelCollector,
    IpmiSensorsCollector,
    LSISASControllerCollector,
    MegaRAIDCollector,
    PowerEdgeRAIDCollector,
    RedfishCollector,
    SsaCLICollector,
)
from prometheus_hardware_exporter.core import Payload


class TestCustomCollector(unittest.TestCase):
    """Custom test class."""

    def test_00_mega_raid_collector_not_installed(self):
        """Test mega raid collector when storcli is not installed."""
        mega_raid_collector = MegaRAIDCollector(Mock())
        mega_raid_collector.sasircu = Mock()
        mega_raid_collector.sasircu.installed = False
        payloads = mega_raid_collector.collect()

        self.assertEqual(len(list(payloads)), 1)

    def test_01_mega_raid_collector_installed_and_okay(self):
        """Test mega raid collector can fetch correct number of metrics."""
        mega_raid_collector = MegaRAIDCollector(Mock())
        mega_raid_collector.storcli = Mock()
        mega_raid_collector.storcli.installed = True

        mock_controllers = {
            0: {
                "enclosures": [
                    {
                        "EID": 251,
                        "State": "OK",
                        "Slots": 2,
                        "PD": 2,
                        "PS": 0,
                        "Fans": 0,
                        "TSs": 0,
                        "Alms": 0,
                        "SIM": 0,
                        "Port#": "2I",
                    }
                ],
                "virtual_drives": [
                    {
                        "DG/VD": "0/239",
                        "TYPE": "RAID1",
                        "State": "Optl",
                        "Access": "RW",
                        "Consist": "Yes",
                        "Cache": "NRWTD",
                        "Cac": "-",
                        "sCC": "ON",
                        "Size": "744.687 GiB",
                        "Name": "NVMe-RAID-1",
                    }
                ],
                "physical_drives": [
                    {
                        "EID:Slt": "251:1",
                        "DID": 0,
                        "State": "Onln",
                        "DG": 0,
                        "Size": "800.00 GB",
                        "Intf": "NVMe",
                        "Med": "SSD",
                        "SED": "N",
                        "PI": "N",
                        "SeSz": "512B",
                        "Model": "MZXLR800HBHQ-000H3                      ",
                        "Sp": "U",
                        "Type": "-",
                    },
                ],
            }
        }
        mega_raid_collector.storcli.get_all_information.return_value = mock_controllers

        payloads = mega_raid_collector.collect()

        available_metrics = [spec.name for spec in mega_raid_collector.specifications]
        self.assertEqual(len(list(payloads)), len(available_metrics))
        for payload in payloads:
            self.assertIn(payload.name, available_metrics)

    def test_10_lsi_sas_2_collector_not_installed(self):
        """Test LSI SAS 2 collector when sas2ircu is not installed."""
        lsi_sas_2_collector = LSISASControllerCollector(2, Mock())
        lsi_sas_2_collector.sasircu = Mock()
        lsi_sas_2_collector.sasircu.installed = False
        lsi_sas_2_collector.sasircu.get_adapters.return_value = {}
        lsi_sas_2_collector.sasircu.get_all_information.return_value = {}
        payloads = lsi_sas_2_collector.collect()

        self.assertEqual(len(list(payloads)), 1)

    def test_11_lsi_sas_2_collector_installed_and_okay(self):
        """Test LSI SAS 2 collector can fetch correct number of metrics."""
        lsi_sas_2_collector = LSISASControllerCollector(2, Mock())
        lsi_sas_2_collector.sasircu = Mock()
        mock_adapters = {
            "0": {
                "Index": "0",
                "Adapter Type": "SAS2008",
                "Vendor ID": "1000h",
                "Device ID": "72h",
                "Pci Address": "00h:05h:00h:00h",
                "SubSys Ven ID": "1028h",
                "SubSys Dev ID": "1f1eh",
            },
        }
        mock_information = {
            "controller": {
                "Controller type": "SAS2008",
                "BIOS version": "7.11.10.00",
                "Firmware version": "7.15.08.00",
                "Channel description": "1 Serial Attached SCSI",
                "Initiator ID": "0",
                "Maximum physical devices": "39",
                "Concurrent commands supported": "2607",
                "Slot": "0",
                "Segment": "0",
                "Bus": "5",
                "Device": "0",
                "Function": "0",
                "RAID Support": "Yes",
            },
            "ir_volumes": {
                "1": {
                    "Volume ID": "286",
                    "PI Supported": "Yes",
                    "PI Enabled": "Yes",
                    "Status of volume": "Okay (OKY)",
                    "Volume wwid": "0677c0fb06777e7b",
                    "RAID level": "RAID1",
                    "Size (in MB)": "139236",
                    "Boot": "Primary",
                    "Physical hard disks": {
                        "PHY[0] Enclosure#/Slot#": "1:0",
                    },
                }
            },
            "enclosures": {
                "1": {
                    "Enclosure#": "1",
                    "Logical ID": "5782bcb0:19e35100",
                    "Numslots": "9",
                    "StartSlot": "0",
                }
            },
            "physical_disks": {
                "1:0": {
                    "Enclosure #": "1",
                    "Slot #": "0",
                    "SAS Address": "4433221-1-0700-0000",
                    "State": "Ready (RDY)",
                    "Size (in MB)/(in sectors)": "476940/976773167",
                    "Manufacturer": "ATA",
                    "Model Number": "ST9500620NS",
                    "Firmware Revision": "AA0D",
                    "Serial No": "9XF3RK3W",
                    "GUID": "5000c5007bc1cfd7",
                    "Protocol": "SATA",
                    "Drive Type": "SATA_HDD",
                },
            },
        }

        lsi_sas_2_collector.sasircu.installed = True
        lsi_sas_2_collector.sasircu.get_adapters.return_value = mock_adapters
        lsi_sas_2_collector.sasircu.get_all_information.return_value = mock_information

        payloads = lsi_sas_2_collector.collect()

        available_metrics = [spec.name for spec in lsi_sas_2_collector.specifications]
        self.assertEqual(len(list(payloads)), len(available_metrics))
        for payload in payloads:
            self.assertIn(payload.name, available_metrics)

    def test_20_lsi_sas_3_collector_not_installed(self):
        """Test LSI SAS 3 collector when sas3ircu is not installed."""
        lsi_sas_3_collector = LSISASControllerCollector(3, Mock())
        lsi_sas_3_collector.sasircu = Mock()
        lsi_sas_3_collector.sasircu.installed = False
        lsi_sas_3_collector.sasircu.get_adapters.return_value = {}
        lsi_sas_3_collector.sasircu.get_all_information.return_value = {}
        payloads = lsi_sas_3_collector.collect()

        self.assertEqual(len(list(payloads)), 1)

    def test_21_lsi_sas_3_collector_installed_and_okay(self):
        """Test LSI SAS 3 collector can fetch correct number of metrics."""
        lsi_sas_3_collector = LSISASControllerCollector(3, Mock())
        lsi_sas_3_collector.sasircu = Mock()
        mock_adapters = {
            "0": {
                "Index": "0",
                "Adapter Type": "SAS3004",
                "Vendor ID": "1000h",
                "Device ID": "97h",
                "Pci Address": "00h:01h:00h:00h",
                "SubSys Ven ID": "1028h",
                "SubSys Dev ID": "1f53h",
            },
        }
        mock_information = {
            "controller": {
                "Controller type": "SAS3008",
                "BIOS version": "8.37.02.00",
                "Firmware version": "16.00.11.00",
                "Channel description": "1 Serial Attached SCSI",
                "Initiator ID": "0",
                "Maximum physical devices": "543",
                "Concurrent commands supported": "9584",
                "Slot": "Unknown",
                "Segment": "0",
                "Bus": "1",
                "Device": "0",
                "Function": "0",
                "RAID Support": "No",
            },
            "ir_volumes": {
                "1": {
                    "Volume ID": "286",
                    "PI Supported": "Yes",
                    "PI Enabled": "Yes",
                    "Status of volume": "Okay (OKY)",
                    "Volume wwid": "0677c0fb06777e7b",
                    "RAID level": "RAID1",
                    "Size (in MB)": "139236",
                    "Boot": "Primary",
                    "Physical hard disks": {
                        "PHY[0] Enclosure#/Slot#": "1:0",
                    },
                }
            },
            "enclosures": {
                "1": {
                    "Enclosure#": "1",
                    "Logical ID": "52cea7f0:c5597b00",
                    "Numslots": "10",
                    "StartSlot": "0",
                },
            },
            "physical_disks": {
                "1:0": {
                    "Enclosure #": "1",
                    "Slot #": "0",
                    "SAS Address": "4433221-1-0400-0000",
                    "State": "Ready (RDY)",
                    "Size (in MB)/(in sectors)": "457862/937703087",
                    "Manufacturer": "ATA",
                    "Model Number": "HFS480G3H2X069N",
                    "Firmware Revision": "DZ00",
                    "Serial No": "BNA7N5994ICB47T3V",
                    "Unit Serial No(VPD)": "BNA7N5994ICB47T3V",
                    "GUID": "5ace42e02532f9e4",
                    "Protocol": "SATA",
                    "Drive Type": "SATA_SSD",
                },
            },
        }

        lsi_sas_3_collector.sasircu.installed = True
        lsi_sas_3_collector.sasircu.get_adapters.return_value = mock_adapters
        lsi_sas_3_collector.sasircu.get_all_information.return_value = mock_information

        payloads = lsi_sas_3_collector.collect()

        available_metrics = [spec.name for spec in lsi_sas_3_collector.specifications]
        self.assertEqual(len(list(payloads)), len(available_metrics))
        for payload in payloads:
            self.assertIn(payload.name, available_metrics)

    def test_30_ipmi_dcmi_collector_not_installed(self):
        """Test ipmi dcmi collector when ipmi-dcmi is not installed."""
        ipmi_dcmi_collector = IpmiDcmiCollector(Mock())
        ipmi_dcmi_collector.ipmi_dcmi = Mock()
        ipmi_dcmi_collector.ipmi_dcmi.installed = False
        ipmi_dcmi_collector.ipmi_dcmi.get_current_power.return_value = {}
        payloads = ipmi_dcmi_collector.collect()

        self.assertEqual(len(list(payloads)), 1)

    def test_31_ipmi_dcmi_collector_installed_and_okay(self):
        """Test ipmi dcmi collector can fetch correct number of metrics."""
        ipmi_dcmi_collector = IpmiDcmiCollector(Mock())
        ipmi_dcmi_collector.ipmi_dcmi = Mock()

        mock_dcmi_payload = {"current_power": 105}

        ipmi_dcmi_collector.ipmi_dcmi.get_current_power.return_value = mock_dcmi_payload

        payloads = ipmi_dcmi_collector.collect()

        available_metrics = [spec.name for spec in ipmi_dcmi_collector.specifications]
        self.assertEqual(len(list(payloads)), len(available_metrics))
        for payload in payloads:
            self.assertIn(payload.name, available_metrics)

    def test_40_ipmi_sel_not_installed(self):
        """Test ipmi sel collector when ipmi sel is not installed."""
        ipmi_sel_collector = IpmiSelCollector(Mock())
        ipmi_sel_collector.ipmi_sel = Mock()
        ipmi_sel_collector.ipmi_sel.installed = False
        ipmi_sel_collector.ipmi_sel.get_sel_entries.return_value = []
        payloads = ipmi_sel_collector.collect()

        self.assertEqual(len(list(payloads)), 1)

    def test_41_ipmi_sel_installed_and_okay(self):
        """Test ipmi sel collector can fetch correct number of metrics."""
        ipmi_sel_collector = IpmiSelCollector(Mock())
        ipmi_sel_collector.ipmi_sel = Mock()

        mock_sel_entries = SAMPLE_IPMI_SEL_ENTRIES

        ipmi_sel_collector.ipmi_sel.get_sel_entries.return_value = mock_sel_entries

        payloads = ipmi_sel_collector.collect()

        payloads_labels_value_map = {}
        for payload in payloads:
            if payload.name == "ipmi_sel_state":
                payloads_labels_value_map[
                    tuple(payload.samples[0].labels.values())
                ] = payload.samples[0].value
        expected_payloads_label_value_map = {
            ("System Board ACPI_Stat", "System ACPI Power State"): 1,
            ("System Chassis SysHealth_Stat", "Chassis"): 2,
        }

        self.assertDictEqual(payloads_labels_value_map, expected_payloads_label_value_map)

    def test_42_ipmi_sel_cmd_fail(self):
        """Test ipmi sel collector when ipmi sel is not installed."""
        ipmi_sel_collector = IpmiSelCollector(Mock())
        ipmi_sel_collector.ipmi_sel = Mock()

        ipmi_sel_collector.ipmi_sel.get_sel_entries.return_value = None

        payloads = list(ipmi_sel_collector.collect())
        assert payloads[0].name == "ipmi_sel_command_success"
        assert payloads[0].samples[0].value == 0.0

    def test_50_ipmimonitoring_not_installed(self):
        """Test ipmi sensor collector when ipmimonitoring is not installed."""
        ipmi_sensors_collector = IpmiSensorsCollector(Mock())
        ipmi_sensors_collector.ipmimonitoring = Mock()
        ipmi_sensors_collector.ipmimonitoring.installed = False
        ipmi_sensors_collector.ipmimonitoring.get_sensor_data.return_value = []
        payloads = ipmi_sensors_collector.collect()

        self.assertEqual(len(list(payloads)), 1)

    def test_51_ipmimonitoring_installed_and_okay(self):
        """Test ipmi sensors collector can fetch correct number of metrics."""
        ipmi_sensors_collector = IpmiSensorsCollector(Mock())
        ipmi_sensors_collector.ipmimonitoring = Mock()

        mock_sensor_data = SAMPLE_IPMI_SENSOR_ENTRIES

        ipmi_sensors_collector.ipmimonitoring.get_sensor_data.return_value = mock_sensor_data
        payloads = ipmi_sensors_collector.collect()

        available_metrics = [spec.name for spec in ipmi_sensors_collector.specifications]
        self.assertEqual(len(list(payloads)), len(mock_sensor_data) + 1)
        for payload in payloads:
            self.assertIn(payload.name, available_metrics)

    def test_60_ssacli_not_installed(self):
        ssacli_collector = SsaCLICollector(Mock())
        ssacli_collector.ssacli = Mock()
        ssacli_collector.ssacli.installed = False
        ssacli_collector.ssacli.get_payload.return_value = {}
        payloads = ssacli_collector.collect()

        self.assertEqual(len(list(payloads)), 1)

    def test_61_ssacli_installed_and_okay(self):
        ssacli_collector = SsaCLICollector(Mock())
        ssacli_collector.ssacli = Mock()
        mock_payload = {
            "2": {
                "controller_status": {"Battery/Capacitor Status": " OK"},
                "ld_status": {"1": "OK"},
                "pd_status": {"2I:0:1": "corrupt"},
            }
        }
        ssacli_collector.ssacli.get_payload.return_value = mock_payload
        payloads = ssacli_collector.collect()

        available_metrics = [spec.name for spec in ssacli_collector.specifications]
        self.assertEqual(len(list(payloads)), len(available_metrics))
        for payload in payloads:
            self.assertIn(payload.name, available_metrics)

    def test_101_perccli_collector_command_success(self):
        with patch.object(PowerEdgeRAIDCollector, "perccli") as mock_cli:
            # 1 success, 1 fail
            mock_cli.ctrl_exists.return_value = True
            mock_cli.ctrl_successes.return_value = {0: False, 1: True}
            mock_cli.get_controllers.return_value = {"count": 1}
            mock_cli.get_virtual_drives.return_value = {}

            power_edge_collector = PowerEdgeRAIDCollector(Mock())
            payloads = list(power_edge_collector.collect())
        assert len(payloads) >= 4

        assert payloads[0].samples[0].value == 1.0
        assert payloads[0].samples[0].name == "perccli_command_success"

        assert payloads[1].samples[0].value == 0.0
        assert payloads[1].samples[0].labels["controller_id"] == "0"
        assert payloads[1].samples[0].name == "perccli_command_ctrl_success"
        assert payloads[2].samples[0].value == 1.0
        assert payloads[2].samples[0].labels["controller_id"] == "1"
        assert payloads[2].samples[0].name == "perccli_command_ctrl_success"

    def test_102_perccli_virtual_device_command_success(self):
        with patch.object(PowerEdgeRAIDCollector, "perccli") as mock_cli:
            mock_cli.success.return_value = True
            mock_cli.ctrl_successes.return_value = {0: False, 1: True}
            mock_cli.get_controllers.return_value = {"count": 1}
            mock_cli.get_virtual_drives.return_value = {
                0: [{"DG": "0", "VD": "0", "cache": "NRWTD", "state": "Optl"}]
            }

            power_edge_collector = PowerEdgeRAIDCollector(Mock())
            payloads = list(power_edge_collector.collect())

        get_payloads = []

        for payload in payloads:
            payload_sample = payload.samples[0]
            get_payloads.append(payload_sample.name)
            if payload_sample.name == "poweredgeraid_virtual_drive":
                assert payload_sample.labels == {"controller_id": "0"}
                assert payload_sample.value == 1
            if payload_sample.name == "poweredgeraid_virtual_drive_info":
                assert payload_sample.labels == {
                    "controller_id": "0",
                    "device_group": "0",
                    "virtual_drive_id": "0",
                    "state": "Optl",
                    "cache_policy": "NRWTD",
                }
                assert payload_sample.value == 1.0
        for name in [
            "poweredgeraid_virtual_drives",
            "poweredgeraid_virtual_drive_info",
        ]:
            assert name in get_payloads

    def test_103_perccli_cmd_fail(self):
        with patch.object(PowerEdgeRAIDCollector, "perccli") as mock_cli:
            mock_cli.success.return_value = False
            power_edge_collector = PowerEdgeRAIDCollector(Mock())
            payloads = list(power_edge_collector.collect())
            assert len(payloads) == 1
            assert payloads[0].samples[0].value == 0.0

    def test_104_perccli_no_controller_exists(self):
        with patch.object(PowerEdgeRAIDCollector, "perccli") as mock_cli:
            mock_cli.success.return_value = True
            mock_cli.ctrl_exists.return_value = False
            power_edge_collector = PowerEdgeRAIDCollector(Mock())
            payloads = list(power_edge_collector.collect())
            assert len(payloads) == 2
            assert payloads[1].samples[0].value == 0.0

    def test_105_perccli_physical_device_command_success(self):
        with patch.object(PowerEdgeRAIDCollector, "perccli") as mock_cli:
            mock_cli.success.return_value = True
            mock_cli.ctrl_successes.return_value = {0: False, 1: True}
            mock_cli.get_controllers.return_value = {"count": 1}
            mock_cli.get_physical_devices.return_value = {
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

            power_edge_collector = PowerEdgeRAIDCollector(Mock())
            payloads = list(power_edge_collector.collect())

        get_payloads = []

        for payload in payloads:
            payload_sample = payload.samples[0]
            get_payloads.append(payload_sample.name)
            if payload_sample.name == "poweredgeraid_physical_device":
                assert payload_sample.labels == {"controller_id": "0"}
                assert payload_sample.value == 2
            if payload_sample.name == "poweredgeraid_physical_device_info":
                labels = payload_sample.labels
                if labels["enclosure_device_id"] == "69" and labels["slot"] == "0":
                    assert payload_sample.labels == {
                        "controller_id": "0",
                        "enclosure_device_id": "69",
                        "slot": "0",
                        "state": "Onln",
                        "device_group": "0",
                        "size": "558.375 GB",
                        "media_type": "HDD",
                    }
                if labels["enclosure_device_id"] == "69" and labels["slot"] == "1":
                    assert payload_sample.labels == {
                        "controller_id": "0",
                        "enclosure_device_id": "69",
                        "slot": "1",
                        "state": "Onln",
                        "device_group": "0",
                        "size": "558.375 GB",
                        "media_type": "HDD",
                    }
                assert payload_sample.value == 1.0
        for name in [
            "poweredgeraid_physical_devices",
            "poweredgeraid_physical_device_info",
        ]:
            assert name in get_payloads

    @patch("prometheus_hardware_exporter.collectors.redfish.redfish.redfish_client")
    @patch(
        "prometheus_hardware_exporter.collectors.redfish.RedfishHelper.get_cached_discover_method"
    )
    def test_200_redfish_no_discovered_services(
        self, mock_get_cached_discover_method, mock_redfish_client
    ):
        """Test redfish collector no redfish services have been discovered."""

        def cached_discover(*args, **kwargs):
            def _discover(*args, **kwargs):
                return False

            return _discover

        mock_get_cached_discover_method.side_effect = cached_discover
        redfish_collector = RedfishCollector(Mock())
        mock_redfish_client.side_effect = ConnectionError

        payloads = redfish_collector.collect()

        # only contains redfish_service_available metric
        self.assertEqual(len(list(payloads)), 1)
        mock_redfish_client.assert_not_called()

    @patch("prometheus_hardware_exporter.collector.logger")
    @patch("prometheus_hardware_exporter.collectors.redfish.redfish.redfish_client")
    @patch(
        "prometheus_hardware_exporter.collectors.redfish.RedfishHelper.get_cached_discover_method"
    )
    def test_201_redfish_no_login(
        self, mock_get_cached_discover_method, mock_redfish_client, mock_logger
    ):
        """Test redfish collector when redfish login doesn't work."""

        def cached_discover(*args, **kwargs):
            def _discover(*args, **kwargs):
                return True

            return _discover

        mock_get_cached_discover_method.side_effect = cached_discover
        redfish_collector = RedfishCollector(Mock())
        redfish_collector.redfish_helper = Mock()

        for err in [
            ConnectionError(),
            InvalidCredentialsError(),
            SessionCreationError(),
            RetriesExhaustedError(),
        ]:
            mock_redfish_client.side_effect = err
            payloads = redfish_collector.collect()

            # Check whether these 2 payloads are present
            # redfish_service_available which is set to value 1
            # redfish_call_success which is set to value 0
            self.assertEqual(len(list(payloads)), 2)
            mock_logger.exception.assert_called_with(
                "Exception occurred while getting redfish object: %s", err
            )
        mock_redfish_client.assert_called()

    @patch("prometheus_hardware_exporter.collector.logger")
    @patch("prometheus_hardware_exporter.collectors.redfish.RedfishHelper.__exit__")
    @patch("prometheus_hardware_exporter.collectors.redfish.RedfishHelper.__enter__")
    @patch("prometheus_hardware_exporter.collectors.redfish.redfish.redfish_client")
    @patch(
        "prometheus_hardware_exporter.collectors.redfish.RedfishHelper.get_cached_discover_method"
    )
    def test_202_redfish_installed_and_okay(
        self,
        mock_get_cached_discover_method,
        mock_redfish_client,
        mock_redfish_helper_enter,
        mock_redfish_helper_exit,
        mock_logger,
    ):
        """Test redfish collector and check if all metrics are present in payload."""
        payloads = []

        def cached_discover(*args, **kwargs):
            def _discover(*args, **kwargs):
                return True

            return _discover

        mock_get_cached_discover_method.side_effect = cached_discover
        redfish_collector = RedfishCollector(Mock())

        mock_helper = Mock()
        mock_redfish_helper_enter.return_value = mock_helper

        mock_get_sensor_data = Mock()
        mock_get_processor_data = Mock()
        mock_get_storage_controller_data = Mock()
        mock_get_network_adapter_data = Mock()
        mock_get_chassis_data = Mock()
        mock_get_storage_drive_data = Mock()
        mock_get_memory_dimm_data = Mock()
        mock_get_smart_storage_health_data = Mock()

        mock_helper.get_sensor_data = mock_get_sensor_data
        mock_helper.get_processor_data = mock_get_processor_data
        mock_helper.get_storage_controller_data = mock_get_storage_controller_data
        mock_helper.get_network_adapter_data = mock_get_network_adapter_data
        mock_helper.get_chassis_data = mock_get_chassis_data
        mock_helper.get_storage_drive_data = mock_get_storage_drive_data
        mock_helper.get_memory_dimm_data = mock_get_memory_dimm_data
        mock_helper.get_smart_storage_health_data = mock_get_smart_storage_health_data

        mock_get_sensor_data.return_value = {
            "1": [
                {"Sensor": "State", "Reading": "Enabled", "Health": "OK"},
                {"Sensor": "HpeServerPowerSupply State", "Reading": "Enabled", "Health": "OK"},
                {
                    "Sensor": "HpeServerPowerSupply LineInputVoltage",
                    "Reading": "208V",
                    "Health": "N/A",
                },
            ]
        }

        processor_count = {"s1": 2, "s2": 1}
        processor_data = {
            "s1": [
                {
                    "processor_id": "p11",
                    "model": "Processor s1 Model 1",
                    "health": "OK",
                    "state": "Enabled",
                },
                {
                    "processor_id": "p12",
                    "model": "Processor s1 Model 2",
                    "health": "NotOK",
                    "state": "Disabled",
                },
            ],
            "s2": [
                {
                    "processor_id": "p21",
                    "model": "Processor s2 Model 1",
                    "health": "OK",
                    "state": "Enabled",
                },
            ],
        }
        mock_get_processor_data.return_value = (
            processor_count,
            processor_data,
        )

        storage_controller_count = {"s1": 2}
        storage_controller_data = {
            "s1": [
                {
                    "storage_id": "STOR1",
                    "controller_id": "sc0",
                    "health": "OK",
                    "state": "Enabled",
                },
                {
                    "storage_id": "STOR2",
                    "controller_id": "sc1",
                    "health": "OK",
                    "state": "Enabled",
                },
            ],
        }
        mock_get_storage_controller_data.return_value = (
            storage_controller_count,
            storage_controller_data,
        )

        # testing for empty metric
        mock_get_network_adapter_data.return_value = {}

        mock_get_chassis_data.return_value = {
            "c1": {
                "chassis_type": "RackMount",
                "manufacturer": "NA",
                "model": "Chassis Model c1",
                "health": "OK",
                "state": "Enabled",
            },
            "c2": {
                "chassis_type": "RackMount",
                "manufacturer": "Dell",
                "model": "Chassis Model c2",
                "health": "OK",
                "state": "Enabled",
            },
        }

        storage_drive_count = {"s1": 2}
        storage_drive_data = {
            "s1": [
                {
                    "storage_id": "STOR1",
                    "drive_id": "d11",
                    "health": "OK",
                    "state": "Enabled",
                },
                {
                    "storage_id": "STOR1",
                    "drive_id": "d12",
                    "health": "OK",
                    "state": "Disabled",
                },
                {
                    "storage_id": "STOR2",
                    "drive_id": "d21",
                    "health": "NA",
                    "state": "Enabled",
                },
            ],
        }
        mock_get_storage_drive_data.return_value = (storage_drive_count, storage_drive_data)

        memory_dimm_count = {"s1": 1, "s2": 1}
        memory_dimm_data = {
            "s1": [
                {
                    "memory_id": "dimm1",
                    "health": "OK",
                    "state": "Enabled",
                },
            ],
            "s2": [
                {
                    "memory_id": "dimm2",
                    "health": "OK",
                    "state": "Enabled",
                },
            ],
        }
        mock_get_memory_dimm_data.return_value = (memory_dimm_count, memory_dimm_data)

        mock_get_smart_storage_health_data.return_value = {
            "c1": {
                "health": "OK",
            }
        }

        payloads = redfish_collector.collect()

        available_metrics = [spec.name for spec in redfish_collector.specifications]
        self.assertEqual(len(list(payloads)), 24)
        for payload in payloads:
            self.assertIn(payload.name, available_metrics)

        mock_logger.warning.assert_called_with(
            "Failed to get %s via redfish", "network_adapter_count"
        )

    def test_203_redfish_create_sensor_metric_payload(self):
        mock_sensor_data = {
            "1": [
                {"Sensor": "State", "Reading": "Enabled", "Health": "OK"},
                {"Sensor": "HpeServerPowerSupply State", "Reading": "Enabled", "Health": "OK"},
                {
                    "Sensor": "HpeServerPowerSupply LineInputVoltage",
                    "Reading": "208V",
                    "Health": "N/A",
                },
            ]
        }
        redfish_collector = RedfishCollector(Mock())
        sensor_payload = redfish_collector._create_sensor_metric_payload(mock_sensor_data)
        self.assertEqual(
            sensor_payload,
            [
                Payload(
                    name="redfish_sensor",
                    value={
                        "chassis": "1",
                        "sensor": "State",
                        "reading": "Enabled",
                        "health": "OK",
                    },
                    labels=[],
                    uuid="redfish_sensor([])",
                ),
                Payload(
                    name="redfish_sensor",
                    value={
                        "chassis": "1",
                        "sensor": "HpeServerPowerSupply State",
                        "reading": "Enabled",
                        "health": "OK",
                    },
                    labels=[],
                    uuid="redfish_sensor([])",
                ),
                Payload(
                    name="redfish_sensor",
                    value={
                        "chassis": "1",
                        "sensor": "HpeServerPowerSupply LineInputVoltage",
                        "reading": "208V",
                        "health": "N/A",
                    },
                    labels=[],
                    uuid="redfish_sensor([])",
                ),
            ],
        )

    def test_204_redfish_create_processor_metric_payload(self):
        mock_processor_count = {"s1": 2, "s2": 1}
        mock_processor_data = {
            "s1": [
                {
                    "processor_id": "p11",
                    "model": "Processor s1 Model 1",
                    "health": "OK",
                    "state": "Enabled",
                },
                {
                    "processor_id": "p12",
                    "model": "Processor s1 Model 2",
                    "health": "NotOK",
                    "state": "Disabled",
                },
            ],
            "s2": [
                {
                    "processor_id": "p21",
                    "model": "Processor s2 Model 1",
                    "health": "OK",
                    "state": "Enabled",
                },
            ],
        }
        redfish_collector = RedfishCollector(Mock())
        processor_payload = redfish_collector._create_processor_metric_payload(
            mock_processor_count, mock_processor_data
        )
        self.assertEqual(
            processor_payload,
            [
                Payload(
                    name="redfish_processors",
                    value=2,
                    labels=["s1"],
                    uuid="redfish_processors(['s1'])",
                ),
                Payload(
                    name="redfish_processor",
                    value={
                        "system_id": "s1",
                        "processor_id": "p11",
                        "model": "Processor s1 Model 1",
                        "health": "OK",
                        "state": "Enabled",
                    },
                    labels=[],
                    uuid="redfish_processor([])",
                ),
                Payload(
                    name="redfish_processor",
                    value={
                        "system_id": "s1",
                        "processor_id": "p12",
                        "model": "Processor s1 Model 2",
                        "health": "NotOK",
                        "state": "Disabled",
                    },
                    labels=[],
                    uuid="redfish_processor([])",
                ),
                Payload(
                    name="redfish_processors",
                    value=1,
                    labels=["s2"],
                    uuid="redfish_processors(['s2'])",
                ),
                Payload(
                    name="redfish_processor",
                    value={
                        "system_id": "s2",
                        "processor_id": "p21",
                        "model": "Processor s2 Model 1",
                        "health": "OK",
                        "state": "Enabled",
                    },
                    labels=[],
                    uuid="redfish_processor([])",
                ),
            ],
        )

    def test_205_redfish_create_storage_controller_metric_payload(self):
        mock_storage_controller_count = {"s1": 2}
        mock_storage_controller_data = {
            "s1": [
                {
                    "storage_id": "STOR1",
                    "controller_id": "sc0",
                    "health": "OK",
                    "state": "Enabled",
                },
                {
                    "storage_id": "STOR2",
                    "controller_id": "sc1",
                    "health": "OK",
                    "state": "Enabled",
                },
            ],
        }
        redfish_collector = RedfishCollector(Mock())
        storage_controller_payload = redfish_collector._create_storage_controller_metric_payload(
            mock_storage_controller_count, mock_storage_controller_data
        )
        self.assertEqual(
            storage_controller_payload,
            [
                Payload(
                    name="redfish_storage_controllers",
                    value=2,
                    labels=["s1"],
                    uuid="redfish_storage_controllers(['s1'])",
                ),
                Payload(
                    name="redfish_storage_controller",
                    value={
                        "system_id": "s1",
                        "storage_id": "STOR1",
                        "controller_id": "sc0",
                        "health": "OK",
                        "state": "Enabled",
                    },
                    labels=[],
                    uuid="redfish_storage_controller([])",
                ),
                Payload(
                    name="redfish_storage_controller",
                    value={
                        "system_id": "s1",
                        "storage_id": "STOR2",
                        "controller_id": "sc1",
                        "health": "OK",
                        "state": "Enabled",
                    },
                    labels=[],
                    uuid="redfish_storage_controller([])",
                ),
            ],
        )

    def test_207_redfish_create_network_adapter_metric_payload(self):
        mock_network_adapter_count = {"c1": 2, "c2": 1}
        redfish_collector = RedfishCollector(Mock())
        network_adapter_payload = redfish_collector._create_network_adapter_metric_payload(
            mock_network_adapter_count
        )
        self.assertEqual(
            network_adapter_payload,
            [
                Payload(
                    name="redfish_network_adapters",
                    value=2,
                    labels=["c1"],
                    uuid="redfish_network_adapters(['c1'])",
                ),
                Payload(
                    name="redfish_network_adapters",
                    value=1,
                    labels=["c2"],
                    uuid="redfish_network_adapters(['c2'])",
                ),
            ],
        )

    def test_206_redfish_create_chassis_metric_payload(self):
        mock_chassis_data = {
            "c1": {
                "chassis_type": "RackMount",
                "manufacturer": "NA",
                "model": "Chassis Model c1",
                "health": "OK",
                "state": "Enabled",
            },
            "c2": {
                "chassis_type": "RackMount",
                "manufacturer": "Dell",
                "model": "Chassis Model c2",
                "health": "OK",
                "state": "Enabled",
            },
        }
        redfish_collector = RedfishCollector(Mock())
        chassis_payload = redfish_collector._create_chassis_metric_payload(mock_chassis_data)
        self.assertEqual(
            chassis_payload,
            [
                Payload(
                    name="redfish_chassis",
                    value={
                        "chassis_id": "c1",
                        "chassis_type": "RackMount",
                        "manufacturer": "NA",
                        "model": "Chassis Model c1",
                        "state": "Enabled",
                        "health": "OK",
                    },
                    labels=[],
                    uuid="redfish_chassis([])",
                ),
                Payload(
                    name="redfish_chassis",
                    value={
                        "chassis_id": "c2",
                        "chassis_type": "RackMount",
                        "manufacturer": "Dell",
                        "model": "Chassis Model c2",
                        "state": "Enabled",
                        "health": "OK",
                    },
                    labels=[],
                    uuid="redfish_chassis([])",
                ),
            ],
        )

    def test_208_redfish_create_storage_drive_metric_payload(self):
        mock_storage_drive_count = {"s1": 3}
        mock_storage_drive_data = {
            "s1": [
                {
                    "storage_id": "STOR1",
                    "drive_id": "d11",
                    "health": "OK",
                    "state": "Enabled",
                },
                {
                    "storage_id": "STOR1",
                    "drive_id": "d12",
                    "health": "OK",
                    "state": "Disabled",
                },
                {
                    "storage_id": "STOR2",
                    "drive_id": "d21",
                    "health": "NA",
                    "state": "Enabled",
                },
            ],
        }
        redfish_collector = RedfishCollector(Mock())
        storage_drive_payload = redfish_collector._create_storage_drive_metric_payload(
            mock_storage_drive_count, mock_storage_drive_data
        )
        self.assertEqual(
            storage_drive_payload,
            [
                Payload(
                    name="redfish_storage_drives",
                    value=3,
                    labels=["s1"],
                    uuid="redfish_storage_drives(['s1'])",
                ),
                Payload(
                    name="redfish_storage_drive",
                    value={
                        "system_id": "s1",
                        "storage_id": "STOR1",
                        "drive_id": "d11",
                        "health": "OK",
                        "state": "Enabled",
                    },
                    labels=[],
                    uuid="redfish_storage_drive([])",
                ),
                Payload(
                    name="redfish_storage_drive",
                    value={
                        "system_id": "s1",
                        "storage_id": "STOR1",
                        "drive_id": "d12",
                        "health": "OK",
                        "state": "Disabled",
                    },
                    labels=[],
                    uuid="redfish_storage_drive([])",
                ),
                Payload(
                    name="redfish_storage_drive",
                    value={
                        "system_id": "s1",
                        "storage_id": "STOR2",
                        "drive_id": "d21",
                        "health": "NA",
                        "state": "Enabled",
                    },
                    labels=[],
                    uuid="redfish_storage_drive([])",
                ),
            ],
        )

    def test_209_redfish_create_memory_dimm_metric_payload(self):
        mock_memory_dimm_count = {"s1": 1, "s2": 1}
        mock_memory_dimm_data = {
            "s1": [
                {
                    "memory_id": "dimm1",
                    "health": "OK",
                    "state": "Enabled",
                },
            ],
            "s2": [
                {
                    "memory_id": "dimm2",
                    "health": "OK",
                    "state": "Enabled",
                },
            ],
        }
        redfish_collector = RedfishCollector(Mock())
        memory_dimm_payload = redfish_collector._create_memory_dimm_metric_payload(
            mock_memory_dimm_count, mock_memory_dimm_data
        )
        self.assertEqual(
            memory_dimm_payload,
            [
                Payload(
                    name="redfish_memory_dimms",
                    value=1,
                    labels=["s1"],
                    uuid="redfish_memory_dimms(['s1'])",
                ),
                Payload(
                    name="redfish_memory_dimm",
                    value={
                        "system_id": "s1",
                        "memory_id": "dimm1",
                        "health": "OK",
                        "state": "Enabled",
                    },
                    labels=[],
                    uuid="redfish_memory_dimm([])",
                ),
                Payload(
                    name="redfish_memory_dimms",
                    value=1,
                    labels=["s2"],
                    uuid="redfish_memory_dimms(['s2'])",
                ),
                Payload(
                    name="redfish_memory_dimm",
                    value={
                        "system_id": "s2",
                        "memory_id": "dimm2",
                        "health": "OK",
                        "state": "Enabled",
                    },
                    labels=[],
                    uuid="redfish_memory_dimm([])",
                ),
            ],
        )

    def test_210_redfish_create_smart_storage_health_metric_payload(self):
        mock_smart_storage_health_data = {"c1": {"health": "OK"}}
        redfish_collector = RedfishCollector(Mock())
        smart_storage_health_payload = (
            redfish_collector._create_smart_storage_health_metric_payload(
                mock_smart_storage_health_data
            )
        )
        self.assertEqual(
            smart_storage_health_payload,
            [
                Payload(
                    name="redfish_smart_storage_health",
                    value=1.0,
                    labels=["c1"],
                    uuid="redfish_smart_storage_health(['c1'])",
                )
            ],
        )
