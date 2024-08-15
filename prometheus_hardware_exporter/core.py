"""Module for collecter core codes."""

from abc import abstractmethod
import threading
import time
from dataclasses import dataclass, field
from logging import getLogger
from typing import Any, Dict, Iterable, List, Type

from prometheus_client.metrics_core import GaugeMetricFamily, Metric
from prometheus_client.registry import Collector

from .config import Config

logger = getLogger(__name__)


@dataclass
class Payload:
    """Container of data for each timeseries."""

    name: str
    value: Any
    labels: List[str] = field(default_factory=list)
    uuid: str = ""  # timeseries's name

    def __post_init__(self) -> None:
        """Create uuid based on metric name and labels."""
        self.uuid = f"{self.name}({self.labels})"


@dataclass
class Specification:
    """Specification for metrics."""

    name: str
    documentation: str
    metric_class: Type[Metric]
    labels: List[str] = field(default_factory=list)


class FetchCache:
    def __init__(self, fetch_function, refresh_interval=5) -> None:
        self.fetch_function = fetch_function
        self.value = None
        self.lock = threading.Lock()
        self.refresh_interval = refresh_interval
        self.refresh_thread = threading.Thread(target=self._refresh_cache)
        self.refresh_thread.daemon = True
        self.refresh_thread.start()

    def _refresh_cache(self) -> None:
        while True:
            start_time = time.time()

            try:
                # Generate the value in the background
                new_value = self.fetch_function()
                with self.lock:
                    self.value = new_value
            except Exception as e:
                print(f"Error in fetch_function: {e}")

            # Calculate time spent fetching
            elapsed_time = time.time() - start_time

            # Wait for the remainder of the refresh interval, if any
            time_to_wait = max(0, self.refresh_interval - elapsed_time)
            time.sleep(time_to_wait)

    def get_value(self) -> Any:
        # Return the precomputed value instantly
        with self.lock:
            return self.value

class BlockingCollector(Collector):
    """Base class for blocking collector.

    BlockingCollector base class is intended to be used when the collector is
    fetching data in a blocking fashion. For example, if the fetching process
    is reading data from files.
    """

    def __init__(self, config: Config, enable_cache: bool = False) -> None:
        """Initialize the class."""
        self.config = config
        self._datastore: Dict[str, Payload] = {}
        self._specs = {spec.name: spec for spec in self.specifications}
        self.cache = None
        if enable_cache:
            self.cache = FetchCache(fetch_function=self.fetch, refresh_interval=5)

    @abstractmethod
    def fetch(self) -> List[Payload]:
        """User defined method for fetching data.

        User should defined their own method for loading data synchronously.
        The return should be a list of `Payload` class; the return value will
        be passed to user defined `process` method that should define how the
        data are used to update the metris.

        Returns:
            A list of payloads to be processed.
        """

    @abstractmethod
    def process(self, payloads: List[Payload], datastore: Dict[str, Payload]) -> List[Payload]:
        """User defined method for processing the fetched data.

        User should defined their own method for processing payloads. This
        includes how to update the metrics using the payloads, and returns the
        processed payload.

        Args:
            payloads: the fetched data to be processed.
            datastore: the data store for holding previous payloads.

        Returns:
            The proecssed payloads.
        """

    @property
    @abstractmethod
    def specifications(self) -> List[Specification]:
        """User defined property that defines the metrics.

        Returns:
            A list of specification.
        """

    @property
    def failed_metrics(self) -> Iterable[Metric]:
        """Defines the metrics to be returned when collector fails.

        Yields:
            metrics: the internal metrics
        """
        # NOTE(dashmage): remove "Collector" from class name to avoid duplication in metric name
        # e.g. `ipmidcmicollector_collector_failed` becomes `ipmidcmi_collector_failed`
        name = self.__class__.__name__.lower().replace("collector", "")
        metric = GaugeMetricFamily(
            name=f"{name}_collector_failed",
            documentation=f"{name} collector failed to fetch metrics",
            labels=["collector"],
        )
        metric.add_metric(
            labels=[name],
            value=1,
        )
        yield metric

    def init_default_datastore(self, payloads: List[Payload]) -> None:
        """Initialize or fill data the store with default values.

        Args:
            payloads: the fetched data to be processed.
        """
        for payload in payloads:
            if payload.uuid not in self._datastore:
                self._datastore[payload.uuid] = Payload(
                    name=payload.name, labels=payload.labels, value=0.0
                )

    def collect(self) -> Iterable[Metric]:
        """Fetch data and update the internal metrics.

        This is a callback method that is used internally within
        `prometheus_client` every time the exporter server is queried. There is
        not return values for this method but it needs to yield all the metrics.

        Yields:
            metrics: the internal metrics
        """
        # The general exception handler will try to make sure the single
        # collector's bug will only change the metrics output to failed_metrics
        # and also make sure other collectors are still working.
        try:
            if self.cache:
                payloads = self.cache.get_value()
            else:
                payloads = self.fetch()
            self.init_default_datastore(payloads)
            processed_payloads = self.process(payloads, self._datastore)

            # unpacked and create metrics
            for payload in processed_payloads:
                spec = self._specs[payload.name]
                # We have to ignore the type checking here, since the subclass of
                # any metric family from prometheus client adds new attributes and
                # methods.
                metric = spec.metric_class(  # type: ignore[call-arg]
                    name=spec.name, labels=spec.labels, documentation=spec.documentation
                )
                metric.add_metric(  # type: ignore[attr-defined]
                    labels=payload.labels, value=payload.value
                )
                yield metric
                self._datastore[payload.uuid] = payload
        except Exception as err:  # pylint: disable=W0718
            logger.error(err)
            yield from self.failed_metrics
