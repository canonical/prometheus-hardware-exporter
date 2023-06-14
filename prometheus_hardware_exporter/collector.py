"""Module for a collection of hardware collecters."""

from logging import getLogger
from typing import Dict, List

from prometheus_client.metrics_core import GaugeMetricFamily, InfoMetricFamily

from .collectors.ipmi_dcmi import IpmiDcmi
from .collectors.ipmi_sel import IpmiSel
from .collectors.ipmimonitoring import IpmiMonitoring
from .collectors.sasircu import LSISASCollectorHelper, Sasircu
from .collectors.storcli import StorCLI
from .core import BlockingCollector, Payload, Specification

logger = getLogger(__name__)


class MegaRAIDCollector(BlockingCollector):
    """Collector for MegaRAID controller."""

    storcli = StorCLI()

    @property
    def specifications(self) -> List[Specification]:
        """Define MegaRAID metric specs."""
        return [
            Specification(
                name="megaraid_controllers",
                documentation="Total number of controllers",
                labels=["hostname"],
                metric_class=GaugeMetricFamily,
            ),
            Specification(
                name="megaraid_virtual_drive",
                documentation="Number of virtual drives",
                labels=["controller_id"],
                metric_class=GaugeMetricFamily,
            ),
            Specification(
                name="megaraid_virtual_drive_state",
                documentation="Indicates the state of virtual drive",
                labels=["controller_id", "virtual_drive_id", "state"],
                metric_class=GaugeMetricFamily,
            ),
            Specification(
                name="megaraid_virtual_drive_cache_policy",
                documentation="Indicates the cache policy of virtual drive",
                labels=["controller_id", "virtual_drive_id", "cache_policy"],
                metric_class=GaugeMetricFamily,
            ),
            Specification(
                name="storcli_command_success",
                documentation="Indicates the if command is successful or not",
                labels=[],
                metric_class=GaugeMetricFamily,
            ),
        ]

    def fetch(self) -> List[Payload]:
        """Load the MegaRAID related information."""
        controller_payload = self.storcli.get_controllers()
        virtual_drives_payload = self.storcli.get_all_virtual_drives()

        if not all([controller_payload, virtual_drives_payload]):
            logger.error(
                "Failed to get MegaRAID controller information using %s", self.storcli.command
            )
            return [
                Payload(
                    name="storcli_command_success",
                    labels=[],
                    value=0.0,
                )
            ]

        payloads = [
            Payload(
                name="megaraid_controllers",
                labels=[controller_payload["hostname"]],
                value=controller_payload["count"],
            ),
            Payload(
                name="storcli_command_success",
                labels=[],
                value=1.0,
            ),
        ]
        for ctrl_id, vds_payload in virtual_drives_payload.items():
            payloads.append(
                Payload(
                    name="megaraid_virtual_drive",
                    labels=[str(ctrl_id)],
                    value=len(vds_payload),
                )
            )
            for vd_payload in vds_payload:
                payloads.append(
                    Payload(
                        name="megaraid_virtual_drive_state",
                        labels=[vd_payload["DG"], vd_payload["VD"], vd_payload["state"]],
                        value=1.0,
                    )
                )
                payloads.append(
                    Payload(
                        name="megaraid_virtual_drive_cache_policy",
                        labels=[vd_payload["DG"], vd_payload["VD"], vd_payload["cache"]],
                        value=1.0,
                    )
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
                labels=[],
                metric_class=GaugeMetricFamily,
            ),
            Specification(
                name="ipmi_dcmi_command_success",
                documentation="Indicates if the ipmi dcmi command is successful or not",
                labels=[],
                metric_class=GaugeMetricFamily,
            ),
        ]

    def fetch(self) -> List[Payload]:
        """Load current power from ipmi dcmi power statistics."""
        current_power_payload = self.ipmi_dcmi.get_current_power()

        if not current_power_payload:
            logger.error("Failed to fetch current power from ipmi dcmi")
            return [Payload(name="ipmi_dcmi_command_success", labels=[], value=0.0)]

        payloads = [
            Payload(
                name="ipmi_dcmi_power_cosumption_watts",
                labels=[],
                value=current_power_payload["current_power"],
            ),
            Payload(name="ipmi_dcmi_command_success", labels=[], value=1.0),
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
                labels=[],
                metric_class=GaugeMetricFamily,
            ),
        ]

    def fetch(self) -> List[Payload]:
        """Load ipmi sensors data."""
        sensor_data = self.ipmimonitoring.get_sensor_data()

        if not sensor_data:
            logger.error("Failed to get ipmi sensor data.")
            return [Payload(name="ipmimonitoring_command_success", labels=[], value=0.0)]

        payloads = [Payload(name="ipmimonitoring_command_success", labels=[], value=1.0)]
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
                labels=[],
                metric_class=GaugeMetricFamily,
            ),
        ]

    def fetch(self) -> List[Payload]:
        """Load ipmi sel entries."""
        sel_entries = self.ipmi_sel.get_sel_entries()

        if not sel_entries:
            logger.error("Failed to get ipmi sel entries.")
            return [Payload(name="ipmi_sel_command_success", labels=[], value=0.0)]

        sel_states_dict = {"NOMINAL": 0, "WARNING": 1, "CRITICAL": 2}

        payloads = [Payload(name="ipmi_sel_command_success", labels=[], value=1.0)]

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
