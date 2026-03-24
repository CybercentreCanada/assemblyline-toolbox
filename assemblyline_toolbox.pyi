"""A collection of compiled utilities to help assemblyline python development."""
# pylint: disable=unused-argument
from typing import Optional


def get_hostip() -> str:
    """A platform specific function to get the current host's ip address."""


class BufferedCalculator:
    """An incremental entropy calculator for large streams of data."""
    def len(self) -> int:
        """Get the number of bytes passed through the calculator."""
    def entropy(self) -> float:
        """Calculate the entropy of the data that has passed through the calculator."""
    def update(self, data: bytes) -> None:
        """Process a chunk of bytes."""


class SsdeepHasher:
    """A wrapper around the ssdeep hash library."""
    def __init__(self, fixed_length: Optional[int] = None):
        """Build a hashing instanece.

        :param int fixed_length: If available, the total number of bytes available.
                                 When provided can enable some optimization.
        """
    def update(self, data: bytes):
        """Process a chunk of bytes."""
    def digest(self) -> str:
        """Calculate the ssdeep hash of all the data processed."""

    @staticmethod
    def hash(data: bytes | str) -> str:
        """Calculate the ssdeep from a buffer."""


class TlshHasher:
    """A wrapper around the tlsh hash library."""
    def __init__(self, fixed_length: Optional[int] = None):
        """Build a hashing instanece."""
    def update(self, data: bytes):
        """Process a chunk of bytes."""
    def digest(self) -> Optional[str]:
        """Calculate the ssdeep hash of all the data processed."""

    @staticmethod
    def hash(data: bytes | str) -> Optional[str]:
        """Calculate the tlsh hash from a buffer."""
