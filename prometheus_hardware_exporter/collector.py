"""Module for a collection of hardware collecters."""

from logging import getLogger
from typing import Dict, List

from prometheus_client.metrics_core import GaugeMetricFamily, InfoMetricFamily

from .collectors.ipmi_dcmi import IpmiDcmi
from .collectors.ipmi_sel import IpmiSel
from .collectors.ipmimonitoring import IpmiMonitoring
from .collectors.perccli import PercCLI
from .collectors.redfish import RedfishHelper
from .collectors.sasircu import LSISASCollectorHelper, Sasircu
from .collectors.ssacli import SsaCLI
from .collectors.storcli import MegaRAIDCollectorHelper, StorCLI
from .config import Config
from .core import BlockingCollector, Payload, Specification

logger = getLogger(__name__)


class PowerEdgeRAIDCollector(BlockingCollector):
    """Collector for PowerEdge RAID controller."""

    perccli = PercCLI()

    @property
    def specifications(self) -> List[Specification]:
        return [
            Specification(
                name="perccli_command_success",
                documentation="Indicates if the command is successful or not",
                metric_class=GaugeMetricFamily,
            ),
            Specification(
                name="perccli_command_ctrl_success",
                documentation="Indicates if the command for each controller is successful or not",
                labels=["controller_id"],
                metric_class=GaugeMetricFamily,
            ),
            Specification(
                name="poweredgeraid_controllers",
                documentation="Total number of controllers",
                metric_class=GaugeMetricFamily,
            ),
            Specification(
                name="poweredgeraid_virtual_drives",
                documentation="Number of virtual drives",
                labels=["controller_id"],
                metric_class=GaugeMetricFamily,
            ),
            Specification(
                name="poweredgeraid_virtual_drive",
                documentation="Indicates the state of virtual drive",
                metric_class=InfoMetricFamily,
            ),
            Specification(
                name="poweredgeraid_physical_devices",
                documentation="Number of physical devices",
                labels=["controller_id"],
                metric_class=GaugeMetricFamily,
            ),
            Specification(
                name="poweredgeraid_physical_device",
                documentation="Indicates the state of physical devices",
                metric_class=InfoMetricFamily,
            ),
        ]

    def fetch(self) -> List[Payload]:
        """Load the PowerEdgeRAID related information."""
        payloads = []
        success = self.perccli.success()
        payloads.append(
            Payload(
                name="perccli_command_success",
                value=1.0 if success else 0.0,
            ),
        )
        if not success:
            return payloads

        ctrl_exists = self.perccli.ctrl_exists()
        if not ctrl_exists:
            payloads.append(
                Payload(
                    name="poweredgeraid_controllers",
                    value=0.0,
                )
            )
            return payloads

        ctrl_sussesses = self.perccli.ctrl_successes()
        for ctrl_id, success in ctrl_sussesses.items():
            payloads.append(
                Payload(
                    name="perccli_command_ctrl_success",
                    labels=[str(ctrl_id)],
                    value=1.0 if success else 0.0,
                ),
            )

        controller_payload = self.perccli.get_controllers()

        payloads.append(
            Payload(
                name="poweredgeraid_controllers",
                value=controller_payload["count"],
            )
        )
        # virtual drive
        virtual_drive_payloads = self.perccli.get_virtual_drives()
        for ctrl_id, vd_payloads in virtual_drive_payloads.items():
            ctrl_id_str = str(ctrl_id)
            payloads.append(
                Payload(
                    name="poweredgeraid_virtual_drives",
                    labels=[ctrl_id_str],
                    value=len(vd_payloads),
                )
            )
            for vd_payload in vd_payloads:
                payloads.append(
                    Payload(
                        name="poweredgeraid_virtual_drive",
                        value={
                            "controller_id": ctrl_id_str,
                            "device_group": vd_payload["DG"],
                            "virtual_drive_id": vd_payload["VD"],
                            "state": vd_payload["state"],
                            "cache_policy": vd_payload["cache"],
                        },
                    )
                )
        # physical device
        physical_device_payloads = self.perccli.get_physical_devices()
        for ctrl_id, pd_payloads in physical_device_payloads.items():
            ctrl_id_str = str(ctrl_id)
            payloads.append(
                Payload(
                    name="poweredgeraid_physical_devices",
                    labels=[ctrl_id_str],
                    value=len(pd_payloads),
                )
            )
            for pd_payload in pd_payloads:
                payloads.append(
                    Payload(
                        name="poweredgeraid_physical_device",
                        value={
                            "controller_id": ctrl_id_str,
                            "device_group": str(pd_payload["DG"]),
                            "enclosure_device_id": pd_payload["eid"],
                            "slot": pd_payload["slt"],
                            "size": pd_payload["size"],
                            "media_type": pd_payload["media_type"],
                            "state": pd_payload["state"],
                        },
                    )
                )
        return payloads

    def process(self, payloads: List[Payload], datastore: Dict[str, Payload]) -> List[Payload]:
        """Process the payload if needed."""
        return payloads


class MegaRAIDCollector(BlockingCollector):
    """Collector for MegaRAID controller."""

    storcli = StorCLI()
    mega_raid_helper = MegaRAIDCollectorHelper()

    @property
    def specifications(self) -> List[Specification]:
        """Define MegaRAID metric specs."""
        return [
            Specification(
                name="megaraid_controllers",
                documentation="Number of MegaRAID controllers",
                metric_class=GaugeMetricFamily,
            ),
            Specification(
                name="megaraid_virtual_drives",
                documentation="Number of virtual drives",
                labels=["controller_id"],
                metric_class=GaugeMetricFamily,
            ),
            Specification(
                name="megaraid_ready_virtual_drives",
                documentation="Number of ready virtual drives",
                labels=["controller_id"],
                metric_class=GaugeMetricFamily,
            ),
            Specification(
                name="megaraid_unready_virtual_drives",
                documentation="Number of unready virtual drives",
                labels=["controller_id"],
                metric_class=GaugeMetricFamily,
            ),
            Specification(
                name="megaraid_virtual_drive",  # will append "_info" internally
                documentation="Shows the information about the virtual drive",
                metric_class=InfoMetricFamily,
            ),
            Specification(
                name="megaraid_physical_drives",
                documentation="Number of physical drives",
                labels=["controller_id"],
                metric_class=GaugeMetricFamily,
            ),
            Specification(
                name="megaraid_physical_drive",  # will append "_info" internally
                documentation="Shows the information about the physical drive",
                metric_class=InfoMetricFamily,
            ),
            Specification(
                name="megaraid_enclosure",  # will append "_info" internally
                documentation="Show the information about the enclosure",
                metric_class=InfoMetricFamily,
            ),
            Specification(
                name="storcli_command_success",
                documentation="Indicates if the command is successful or not",
                metric_class=GaugeMetricFamily,
            ),
        ]

    def fetch(self) -> List[Payload]:
        """Load the MegaRAID related information."""
        controllers = self.storcli.get_all_information()

        if not controllers:
            logger.error(
                "Failed to get MegaRAID controller information using %s", self.storcli.command
            )
            return [Payload(name="storcli_command_success", value=0.0)]

        payloads = [
            Payload(
                name="megaraid_controllers",
                value=len(controllers),
            ),
            Payload(
                name="storcli_command_success",
                value=1.0,
            ),
        ]
        for idx, controller in controllers.items():
            idx = str(idx)

            # Add integrated RAID volume metrics
            virtual_drives = self.mega_raid_helper.extract_virtual_drives(
                idx, controller["virtual_drives"]
            )
            virtual_drive_state_counts = self.mega_raid_helper.count_virtual_drive_state(
                virtual_drives, state={"Optl"}
            )
            payloads.extend(
                [
                    Payload(name="megaraid_virtual_drive", value=virtual_drive)
                    for virtual_drive in virtual_drives
                ]
            )
            payloads.extend(
                [
                    Payload(
                        name="megaraid_virtual_drives",
                        labels=[idx],
                        value=virtual_drive_state_counts[0],
                    ),
                    Payload(
                        name="megaraid_ready_virtual_drives",
                        labels=[idx],
                        value=virtual_drive_state_counts[1],
                    ),
                    Payload(
                        name="megaraid_unready_virtual_drives",
                        labels=[idx],
                        value=virtual_drive_state_counts[2],
                    ),
                ]
            )

            # Add physical drive metrics
            physical_drives = self.mega_raid_helper.extract_physical_drives(
                idx, controller["physical_drives"]
            )
            payloads.extend(
                [
                    Payload(name="megaraid_physical_drive", value=physical_drive)
                    for physical_drive in physical_drives
                ]
            )
            payloads.append(
                Payload(
                    name="megaraid_physical_drives",
                    labels=[idx],
                    value=len(controller["physical_drives"]),
                ),
            )

            # Add enclosure metrics
            enclosures = self.mega_raid_helper.extract_enclosures(idx, controller["enclosures"])
            payloads.extend(
                [Payload(name="megaraid_enclosure", value=enclosure) for enclosure in enclosures]
            )
        return payloads

    def process(self, payloads: List[Payload], datastore: Dict[str, Payload]) -> List[Payload]:
        """Process the payload if needed."""
        return payloads


class IpmiDcmiCollector(BlockingCollector):
    """Collector for ipmi dcmi metrics."""

    ipmi_dcmi = IpmiDcmi()

    @property
    def specifications(self) -> List[Specification]:
        """Define dcmi metric specs."""
        return [
            Specification(
                name="ipmi_dcmi_power_cosumption_watts",
                documentation="Current power consumption in watts",
                metric_class=GaugeMetricFamily,
            ),
            Specification(
                name="ipmi_dcmi_command_success",
                documentation="Indicates if the ipmi dcmi command is successful or not",
                metric_class=GaugeMetricFamily,
            ),
        ]

    def fetch(self) -> List[Payload]:
        """Load current power from ipmi dcmi power statistics."""
        current_power_payload = self.ipmi_dcmi.get_current_power()

        if not current_power_payload:
            logger.error("Failed to fetch current power from ipmi dcmi")
            return [Payload(name="ipmi_dcmi_command_success", value=0.0)]

        payloads = [
            Payload(
                name="ipmi_dcmi_power_cosumption_watts",
                value=current_power_payload["current_power"],
            ),
            Payload(name="ipmi_dcmi_command_success", value=1.0),
        ]
        return payloads

    def process(self, payloads: List[Payload], datastore: Dict[str, Payload]) -> List[Payload]:
        """Process the payload if needed."""
        return payloads


class IpmiSensorsCollector(BlockingCollector):
    """Collector for ipmi sensors data."""

    ipmimonitoring = IpmiMonitoring()

    @property
    def specifications(self) -> List[Specification]:
        """Define ipmi sensors metrics specs."""
        return [
            Specification(
                name="ipmi_temperature_celsius",
                documentation="Temperature measure from temperature sensors",
                labels=["name", "state", "unit"],
                metric_class=GaugeMetricFamily,
            ),
            Specification(
                name="ipmi_power_watts",
                documentation="Power measure from power sensors",
                labels=["name", "state", "unit"],
                metric_class=GaugeMetricFamily,
            ),
            Specification(
                name="ipmi_voltage_volts",
                documentation="Voltage measure from voltage sensors",
                labels=["name", "state", "unit"],
                metric_class=GaugeMetricFamily,
            ),
            Specification(
                name="ipmi_current_amperes",
                documentation="Current measure from current sensors",
                labels=["name", "state", "unit"],
                metric_class=GaugeMetricFamily,
            ),
            Specification(
                name="ipmi_fan_speed_rpm",
                documentation="Fan speed measure, in rpm",
                labels=["name", "state", "unit"],
                metric_class=GaugeMetricFamily,
            ),
            Specification(
                name="ipmi_fan_speed_ratio",
                documentation="Fan speed measure, as a percentage of maximum speed",
                labels=["name", "state", "unit"],
                metric_class=GaugeMetricFamily,
            ),
            Specification(
                name="ipmi_generic_sensor_value",
                documentation="Generic sensor value from ipmi sensors",
                labels=["name", "state", "unit", "type"],
                metric_class=GaugeMetricFamily,
            ),
            Specification(
                name="ipmimonitoring_command_success",
                documentation="Indicates if the ipmimonitoring command succeeded or not",
                metric_class=GaugeMetricFamily,
            ),
        ]

    def fetch(self) -> List[Payload]:
        """Load ipmi sensors data."""
        sensor_data = self.ipmimonitoring.get_sensor_data()

        if not sensor_data:
            logger.error("Failed to get ipmi sensor data.")
            return [Payload(name="ipmimonitoring_command_success", value=0.0)]

        payloads = [Payload(name="ipmimonitoring_command_success", value=1.0)]
        for sensor_data_item in sensor_data:
            current_item_unit = sensor_data_item.get("Units")
            if current_item_unit == "C":
                payloads.append(
                    self._create_sensor_data_payload(sensor_data_item, "ipmi_temperature_celsius")
                )
            elif current_item_unit == "RPM":
                payloads.append(
                    self._create_sensor_data_payload(sensor_data_item, "ipmi_fan_speed_rpm")
                )
            elif current_item_unit == "A":
                payloads.append(
                    self._create_sensor_data_payload(sensor_data_item, "ipmi_current_amperes")
                )
            elif current_item_unit == "V":
                payloads.append(
                    self._create_sensor_data_payload(sensor_data_item, "ipmi_voltage_volts")
                )
            elif current_item_unit == "W":
                payloads.append(
                    self._create_sensor_data_payload(sensor_data_item, "ipmi_power_watts")
                )
            elif current_item_unit == "%":
                if sensor_data_item.get("Type") == "Fan":
                    payloads.append(
                        self._create_sensor_data_payload(sensor_data_item, "ipmi_fan_speed_ratio")
                    )
                else:
                    payloads.append(
                        self._create_sensor_data_payload(
                            sensor_data_item, "ipmi_generic_sensor_value"
                        )
                    )
            else:
                payloads.append(
                    self._create_sensor_data_payload(sensor_data_item, "ipmi_generic_sensor_value")
                )

        return payloads

    def process(self, payloads: List[Payload], datastore: Dict[str, Payload]) -> List[Payload]:
        """Process the payload if needed."""
        return payloads

    def _create_sensor_data_payload(
        self, sensor_data_item: Dict[str, str], metric_name: str
    ) -> Payload:
        """Create a payload based on metric name and sensor data."""
        if metric_name == "ipmi_generic_sensor_value":
            return Payload(
                name=metric_name,
                labels=[
                    sensor_data_item["Name"],
                    sensor_data_item["State"],
                    sensor_data_item["Units"],
                    sensor_data_item["Type"],
                ],
                value=self._get_sensor_value_from_reading(sensor_data_item["Reading"]),
            )

        return Payload(
            name=metric_name,
            labels=[
                sensor_data_item["Name"],
                sensor_data_item["State"],
                sensor_data_item["Units"],
            ],
            value=self._get_sensor_value_from_reading(sensor_data_item["Reading"]),
        )

    def _get_sensor_value_from_reading(self, reading: str) -> float:
        """Get sensor value as a float from sensor reading.

        Returns:
            a floating point of the sensor reading, or 0.0
        """
        try:
            return float(reading)
        except ValueError:
            logger.info("Changing sensor data value %s to 0.0", reading)
            return 0.0


class IpmiSelCollector(BlockingCollector):
    """Collector for IPMI SEL data."""

    ipmi_sel = IpmiSel()

    @property
    def specifications(self) -> List[Specification]:
        """Define IPMI SEL metrics specs."""
        return [
            Specification(
                name="ipmi_sel_state",
                documentation="Event state from IPMI SEL entry.",
                labels=["name", "type"],
                metric_class=GaugeMetricFamily,
            ),
            Specification(
                name="ipmi_sel_command_success",
                documentation="Indicates if the ipmi sel command succeeded or not",
                metric_class=GaugeMetricFamily,
            ),
        ]

    def fetch(self) -> List[Payload]:
        """Load ipmi sel entries."""
        sel_entries = self.ipmi_sel.get_sel_entries(self.config.ipmi_sel_interval)

        if sel_entries is None:
            logger.warning("No recent ipmi sel entries to collect.")
            return [Payload(name="ipmi_sel_command_success", value=0.0)]

        sel_states_dict = {"NOMINAL": 0, "WARNING": 1, "CRITICAL": 2}

        payloads = [Payload(name="ipmi_sel_command_success", value=1.0)]

        sel_entries_dict: Dict[tuple, int] = {}
        for sel_entry in sel_entries:
            if sel_entry["State"].upper() in sel_states_dict:
                sel_state_value = sel_states_dict[sel_entry["State"].upper()]
            else:
                logger.warning(
                    "Unknown ipmi SEL state: %s. Treating it as Nominal.", sel_entry["State"]
                )
                sel_state_value = sel_states_dict["NOMINAL"]

            key = (sel_entry["Name"], sel_entry["Type"])
            if key not in sel_entries_dict or sel_entries_dict[key] < sel_state_value:
                sel_entries_dict[key] = sel_state_value

        for sel_labels, sel_state_value in sel_entries_dict.items():
            payloads.append(
                Payload(
                    name="ipmi_sel_state",
                    labels=list(sel_labels),
                    value=sel_state_value,
                )
            )
        return payloads

    def process(self, payloads: List[Payload], datastore: Dict[str, Payload]) -> List[Payload]:
        """Process the payload if needed."""
        return payloads


class LSISASControllerCollector(BlockingCollector):
    """Collector for LSI SAS controllers."""

    def __init__(self, version: int, config: Config) -> None:
        """Initialize the collector."""
        self.version = version
        self.sasircu = Sasircu(version)
        self.lsi_sas_helper = LSISASCollectorHelper()
        super().__init__(config)

    @property
    def specifications(self) -> List[Specification]:
        """Define LSI SAS metric specs."""
        return [
            Specification(
                name=f"lsi_sas_{self.version}_controllers",
                documentation="Number of LSI SAS-{self.version} controllers",
                metric_class=GaugeMetricFamily,
            ),
            Specification(
                name=f"lsi_sas_{self.version}_ir_volumes",
                documentation="Number of IR volumes",
                labels=["controller_id"],
                metric_class=GaugeMetricFamily,
            ),
            Specification(
                name=f"lsi_sas_{self.version}_ready_ir_volumes",
                documentation="Number of ready IR volumes",
                labels=["controller_id"],
                metric_class=GaugeMetricFamily,
            ),
            Specification(
                name=f"lsi_sas_{self.version}_unready_ir_volumes",
                documentation="Number of unready IR volumes",
                labels=["controller_id"],
                metric_class=GaugeMetricFamily,
            ),
            Specification(
                name=f"lsi_sas_{self.version}_ir_volume",  # will append "_info" internally
                documentation="Shows the information about the integrated RAID volume",
                metric_class=InfoMetricFamily,
            ),
            Specification(
                name=f"lsi_sas_{self.version}_physical_devices",
                documentation="Number of physical devices",
                labels=["controller_id"],
                metric_class=GaugeMetricFamily,
            ),
            Specification(
                name=f"lsi_sas_{self.version}_ready_physical_devices",
                documentation="Number of ready physical devices",
                labels=["controller_id"],
                metric_class=GaugeMetricFamily,
            ),
            Specification(
                name=f"lsi_sas_{self.version}_unready_physical_devices",
                documentation="Number of unready physical devices",
                labels=["controller_id"],
                metric_class=GaugeMetricFamily,
            ),
            Specification(
                name=f"lsi_sas_{self.version}_physical_device",  # will append "_info" internally
                documentation="Shows the information about the physical device",
                metric_class=InfoMetricFamily,
            ),
            Specification(
                name=f"lsi_sas_{self.version}_enclosure",  # will append "_info" internally
                documentation="Show the information about the enclosure",
                metric_class=InfoMetricFamily,
            ),
            Specification(
                name=f"sas{self.version}ircu_command_success",
                documentation="Indicates if the command is successful or not",
                metric_class=GaugeMetricFamily,
            ),
        ]

    def fetch(self) -> List[Payload]:
        """Load the LSI SAS controllers related information."""
        adapters = self.sasircu.get_adapters()
        all_information = [(idx, self.sasircu.get_all_information(idx)) for idx in adapters]

        if not all([adapters, all_information]):
            logger.error(
                "Failed to get LSI SAS-%d controller information using %s",
                self.version,
                self.sasircu.command,
            )
            return [Payload(name=f"sas{self.version}ircu_command_success", value=0.0)]

        payloads = [
            Payload(
                name=f"lsi_sas_{self.version}_controllers",
                value=len(adapters),
            ),
            Payload(
                name=f"sas{self.version}ircu_command_success",
                value=1.0,
            ),
        ]

        for idx, info in all_information:
            # Add integrated RAID volume metrics
            ir_volumes = self.lsi_sas_helper.extract_ir_volumes(idx, info)
            ir_volume_state_counts = self.lsi_sas_helper.count_ir_volume_state(
                ir_volumes, {"Okay (OKY)"}
            )
            payloads.extend(
                [
                    Payload(
                        name=f"lsi_sas_{self.version}_ir_volume",
                        value=ir_volume,
                    )
                    for ir_volume in ir_volumes
                ]
            )
            payloads.extend(
                [
                    Payload(
                        name=f"lsi_sas_{self.version}_ir_volumes",
                        labels=[idx],
                        value=ir_volume_state_counts[0],
                    ),
                    Payload(
                        name=f"lsi_sas_{self.version}_ready_ir_volumes",
                        labels=[idx],
                        value=ir_volume_state_counts[1],
                    ),
                    Payload(
                        name=f"lsi_sas_{self.version}_unready_ir_volumes",
                        labels=[idx],
                        value=ir_volume_state_counts[2],
                    ),
                ]
            )

            # Add physical disk metrics
            physical_disks = self.lsi_sas_helper.extract_physical_disks(idx, info)
            physical_disks_state_counts = self.lsi_sas_helper.count_physical_disk_state(
                physical_disks, {"Ready (RDY)", "Optimal (OPT)"}
            )
            payloads.extend(
                [
                    Payload(name=f"lsi_sas_{self.version}_physical_device", value=ir_volume)
                    for ir_volume in ir_volumes
                ]
            )
            payloads.extend(
                [
                    Payload(
                        name=f"lsi_sas_{self.version}_physical_devices",
                        labels=[idx],
                        value=physical_disks_state_counts[0],
                    ),
                    Payload(
                        name=f"lsi_sas_{self.version}_ready_physical_devices",
                        labels=[idx],
                        value=physical_disks_state_counts[1],
                    ),
                    Payload(
                        name=f"lsi_sas_{self.version}_unready_physical_devices",
                        labels=[idx],
                        value=physical_disks_state_counts[2],
                    ),
                ]
            )

            # Add enclosure metrics
            payloads.extend(
                [
                    Payload(name=f"lsi_sas_{self.version}_enclosure", value=enclosure)
                    for enclosure in self.lsi_sas_helper.extract_enclosures(idx, info)
                ]
            )
        return payloads

    def process(self, payloads: List[Payload], datastore: Dict[str, Payload]) -> List[Payload]:
        """Process the payload if needed."""
        return payloads


class SsaCLICollector(BlockingCollector):
    """Collector for storage arrays that support ssacli."""

    ssacli = SsaCLI()

    @property
    def specifications(self) -> List[Specification]:
        return [
            Specification(
                name="ssacli_command_success",
                documentation="Indicates if the command is successful or not",
                metric_class=GaugeMetricFamily,
            ),
            Specification(
                name="ssacli_controllers",
                documentation="Total number of controllers",
                metric_class=GaugeMetricFamily,
            ),
            Specification(
                name="ssacli_controller",
                documentation="Shows the information about controller part",
                metric_class=InfoMetricFamily,
            ),
            Specification(
                name="ssacli_logical_drives",
                documentation="The number of logical drives in the slot",
                labels=["slot"],
                metric_class=GaugeMetricFamily,
            ),
            Specification(
                name="ssacli_physical_drives",
                documentation="The number of physical drives in the slot",
                labels=["slot"],
                metric_class=GaugeMetricFamily,
            ),
            Specification(
                name="ssacli_logical_drive",
                documentation="Shows the information about logical drive",
                metric_class=InfoMetricFamily,
            ),
            Specification(
                name="ssacli_physical_drive",
                documentation="Shows the information about physical drive",
                metric_class=InfoMetricFamily,
            ),
        ]

    def fetch(self) -> List[Payload]:
        """Load the controller and drive status using ssacli tool."""
        ssacli_payload = self.ssacli.get_payload()

        if not ssacli_payload:
            logger.error("Failed to get controllers info using ssacli.")
            return [Payload(name="ssacli_command_success", value=0.0)]
        payloads = [
            Payload(name="ssacli_command_success", value=1.0),
            Payload(name="ssacli_controllers", value=len(ssacli_payload)),
        ]

        for slot, payload in ssacli_payload.items():
            ctrl_status = payload["controller_status"]
            for part, status in ctrl_status.items():
                payloads.append(
                    Payload(
                        name="ssacli_controller",
                        value={"slot": slot, "part": part, "status": status},
                    )
                )
            ld_status = payload["ld_status"]
            payloads.append(
                Payload(name="ssacli_logical_drives", labels=[slot], value=len(ld_status))
            )
            for drive_id, status in ld_status.items():
                payloads.append(
                    Payload(
                        name="ssacli_logical_drive",
                        value={"slot": slot, "drive_id": drive_id, "status": status},
                    )
                )
            pd_status = payload["pd_status"]
            payloads.append(
                Payload(name="ssacli_physical_drives", labels=[slot], value=len(pd_status))
            )
            for drive_id, status in pd_status.items():
                payloads.append(
                    Payload(
                        name="ssacli_physical_drive",
                        value={"slot": slot, "drive_id": drive_id, "status": status},
                    )
                )

        return payloads

    def process(self, payloads: List[Payload], datastore: Dict[str, Payload]) -> List[Payload]:
        """Process the payload if needed."""
        return payloads


class RedfishCollector(BlockingCollector):
    """Collector for redfish status and data."""

    redfish_helper = RedfishHelper()

    @property
    def specifications(self) -> List[Specification]:
        """Define specs for redfish metrics."""
        return [
            Specification(
                name="redfish_call_success",
                documentation="Indicates if call to the redfish API succeeded or not.",
                metric_class=GaugeMetricFamily,
            ),
            Specification(
                name="redfish_service_available",
                documentation="Indicates if redfish service is available or not on the system.",
                metric_class=GaugeMetricFamily,
            ),
            Specification(
                name="redfish_sensor",
                documentation="Sensor information obtained from redfish.",
                metric_class=InfoMetricFamily,
            ),
        ]

    def fetch(self) -> List[Payload]:
        """Load redfish data."""
        redfish_host = self.config.redfish_host
        redfish_username = self.config.redfish_username
        redfish_password = self.config.redfish_password
        payloads = []
        service_status = self.redfish_helper.discover()
        payloads.append(Payload(name="redfish_service_available", value=float(service_status)))

        sensor_data = self.redfish_helper.get_sensor_data(
            host=redfish_host,
            username=redfish_username,
            password=redfish_password,
        )
        if not sensor_data:
            logger.error("Failed to get sensor data via redfish.")
            payloads.append(Payload(name="redfish_call_success", value=0.0))
            return payloads

        payloads.append(Payload(name="redfish_call_success", value=1.0))
        for chassis_name, curr_sensor_data in sensor_data.items():
            for sensor_data_item in curr_sensor_data:
                payloads.append(
                    Payload(
                        name="redfish_sensor",
                        value={
                            "chassis": chassis_name,
                            "sensor": sensor_data_item["Sensor"],
                            "reading": sensor_data_item["Reading"],
                            "health": sensor_data_item["Health"],
                        },
                    )
                )

        return payloads

    def process(self, payloads: List[Payload], datastore: Dict[str, Payload]) -> List[Payload]:
        """Process the payload if needed."""
        return payloads
