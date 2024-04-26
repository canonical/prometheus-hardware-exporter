"""Module for hardware exporter."""

import threading
from logging import getLogger
from socketserver import ThreadingMixIn
from typing import Any
from wsgiref.simple_server import WSGIRequestHandler, WSGIServer, make_server

from prometheus_client import make_wsgi_app
from prometheus_client.core import REGISTRY
from prometheus_client.registry import Collector

logger = getLogger(__name__)


class ThreadingWSGIServer(ThreadingMixIn, WSGIServer):
    """A WSGI server that handle requests in a separate thread."""

    daemon_threads = True


class SilentRequestHandler(WSGIRequestHandler):
    """A Silent Request handler."""

    def log_message(self, format: str, *args: Any) -> None:  # pylint: disable=W0622
        """Log nothing."""


class Exporter:
    """The exporter class."""

    def __init__(self, port: int, addr: str = "0.0.0.0") -> None:
        """Initialize the exporter class.

        Args:
            port: Start the exporter at this port.
            addr: Start the exporter at this address.
        """
        self.addr = addr
        self.port = int(port)
        self.app = make_wsgi_app()

    def register(self, collector: Collector) -> None:
        """Register collector to the exporter."""
        REGISTRY.register(collector)

    def run(self, daemon: bool = False) -> None:
        """Start the exporter server."""
        httpd = make_server(
            self.addr,
            self.port,
            self.app,
            server_class=ThreadingWSGIServer,
            handler_class=SilentRequestHandler,
        )
        logger.info("Started prometheus hardware exporter at %s:%s.", self.addr, self.port)
        thread = threading.Thread(target=httpd.serve_forever)
        thread.daemon = daemon
        thread.start()
