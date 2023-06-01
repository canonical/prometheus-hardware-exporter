"""Module for helper functions."""

import subprocess
from logging import getLogger
from typing import Optional, Tuple

logger = getLogger(__name__)


class CommandNotFoundError(Exception):
    """Command not found error."""


class CommandExecutionError(Exception):
    """Command excution error error."""


class Command:
    """Generic wrapper for command line tool."""

    prefix = ""
    command = ""
    installed = False

    def __init__(self) -> None:
        """Initialize the Command class."""
        self.installed = self.check_installed()

    def __call__(self, args: Optional[str] = None) -> Tuple[Optional[str], Optional[Exception]]:
        """Run the command, and return the result and error.

        Returns:
            result: output of the command or None
            error: an exception of None
        """
        if not self.installed:
            error = CommandNotFoundError(f"{self.command} not installed.")
            logger.error(str(error))
            return None, error

        result, error = self.check_output(args=args)  # type: ignore[assignment]
        if error:
            logger.error(str(error))
            return None, error
        return result, error

    def check_installed(self) -> bool:
        """Check if the command is installed or not.

        Returns:
            True if the command can be found else False.
        """
        _, error = self.check_output(prefix="", command=f"which {self.command}")
        if error:
            return False
        return True

    def check_output(
        self,
        prefix: Optional[str] = None,
        command: Optional[str] = None,
        args: Optional[str] = None,
    ) -> Tuple[Optional[str], Optional[CommandExecutionError]]:
        """Run the command, and return the result and error.

        Returns:
            result: output of the command or None
            error: an exception of None
        """
        error = None
        result = None
        args = args if args is not None else ""
        prefix = prefix if prefix is not None else self.prefix
        command = command if command is not None else self.command
        full_command = " ".join([prefix, command, args]).strip()

        logger.debug("Running command: %s", full_command)
        try:
            result = subprocess.check_output(full_command, shell=True).decode().strip()
        except subprocess.CalledProcessError as err:
            error = CommandExecutionError(err)
        return result, error
