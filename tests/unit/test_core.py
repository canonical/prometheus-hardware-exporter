import unittest
from unittest.mock import Mock, patch

import pytest

from prometheus_hardware_exporter.core import BlockingCollector, Payload, Specification


class TestBlockingCollector(unittest.TestCase):
    """BlockingCollector test class."""

    def setUp(self):
        self.mock_payloads = [Payload(name="abc", labels=[], value=0)]
        self.mock_specifications = [
            Specification(name="abc", documentation="", labels=[], metric_class=Mock())
        ]

    def test_cannot_init_collector_base(self):
        """Test cannot initialize CollectorBase."""
        with pytest.raises(TypeError):
            BlockingCollector()

    @patch.multiple(BlockingCollector, __abstractmethods__=set())
    def test_sync_collector_class_collect(self):
        """Test sync collector class's collect method."""
        BlockingCollector.fetch = Mock(return_value=self.mock_payloads)
        BlockingCollector.process = Mock(return_value=self.mock_payloads)
        BlockingCollector.specifications = self.mock_specifications
        self.test_subclass = BlockingCollector(Mock())
        list(self.test_subclass.collect())  # need list() because it's a generator
        self.test_subclass.fetch.assert_called()
        self.test_subclass.process.assert_called()
