"""Module for helper functions."""

import json
import subprocess
from dataclasses import dataclass
from logging import getLogger
from typing import Optional, Union

logger = getLogger(__name__)


@dataclass
class Result:
    """Result represents the outcome of a subprocess call."""

    data: str = ""
    error: Optional[Exception] = None


class Command:
    """Generic wrapper for command line tool."""

    prefix = ""
    command = ""

    def __init__(self) -> None:
        """Initialize the Command class."""
        self.installed = False
        result = self.check_output(prefix="", command=f"which {self.command}")
        if not result.error:
            self.installed = True

    def __call__(self, args: Optional[str] = None) -> Result:
        """Run the command, and return the result and error.

        Returns:
            result: an instance of Result class
        """
        if not self.installed:
            error = ValueError(f"{self.command} not installed.")
            logger.error(error)
            return Result(error=error)

        return self.check_output(args=args)

    def check_output(
        self,
        prefix: Optional[str] = None,
        command: Optional[str] = None,
        args: Optional[str] = None,
    ) -> Result:
        """Run the command, and return the result.

        Returns:
            result: an instance of Result class
        """
        result = Result()
        args = args if args is not None else ""
        prefix = prefix if prefix is not None else self.prefix
        command = command if command is not None else self.command
        full_command = " ".join([prefix, command, args]).strip()
        try:
            logger.debug("Running command: %s", full_command)
            result.data = subprocess.check_output(full_command, shell=True).decode().strip()
        except subprocess.CalledProcessError as err:
            logger.error(err)
            result.error = err
        return result


def get_json_output(content: str) -> Union[dict, Exception]:
    """Load json string and return Result."""
    try:
        data = json.loads(content)
        return data
    except ValueError as err:
        return err
