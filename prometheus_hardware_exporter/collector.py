"""Module for a collection of hardware collecters."""

from logging import getLogger
from typing import Dict, List

from prometheus_client.metrics_core import GaugeMetricFamily, InfoMetricFamily

from .collectors.ipmi_dcmi import IpmiDcmi
from .collectors.ipmi_sel import IpmiSel
from .collectors.ipmimonitoring import IpmiMonitoring
from .collectors.perccli import PercCLI
from .collectors.sasircu import LSISASCollectorHelper, Sasircu
from .collectors.storcli import MegaRAIDCollectorHelper, StorCLI
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
                            "device_group": pd_payload["DG"],
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
        sel_entries = self.ipmi_sel.get_sel_entries()

        if not sel_entries:
            logger.error("Failed to get ipmi sel entries.")
            return [Payload(name="ipmi_sel_command_success", value=0.0)]

        sel_states_dict = {"NOMINAL": 0, "WARNING": 1, "CRITICAL": 2}

        payloads = [Payload(name="ipmi_sel_command_success", value=1.0)]

        for sel_entry in sel_entries:
            payloads.append(
                Payload(
                    name="ipmi_sel_state",
                    labels=[
                        sel_entry["Name"],
                        sel_entry["Type"],
                    ],
                    value=sel_states_dict[sel_entry["State"].upper()],
                )
            )
        return payloads

    def process(self, payloads: List[Payload], datastore: Dict[str, Payload]) -> List[Payload]:
        """Process the payload if needed."""
        return payloads


class LSISASControllerCollector(BlockingCollector):
    """Collector for LSI SAS controllers."""

    def __init__(self, version: int) -> None:
        """Initialize the collector."""
        self.version = version
        self.sasircu = Sasircu(version)
        self.lsi_sas_helper = LSISASCollectorHelper()
        super().__init__()

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
