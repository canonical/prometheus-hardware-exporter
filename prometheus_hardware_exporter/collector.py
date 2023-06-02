"""Module for a collection of hardware collecters."""

from logging import getLogger
from typing import Dict, List

from prometheus_client.metrics_core import GaugeMetricFamily

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
