from __future__ import annotations

import os
import uuid
from inspect import getmembers, isfunction
from sys import exc_info
from traceback import format_tb
from typing import AnyStr, Iterable, Optional


# ---------------------------------------------------------------------------
# Exception helpers
# ---------------------------------------------------------------------------

class TransportException(Exception):
    """FileTransport exception base class."""

    def __init__(self, message, cause=None):
        Exception.__init__(self, message)
        self.cause = cause


class _Chain:
    """Method decorator that wraps exceptions as *exception_class*."""

    def __init__(self, exception):
        self.exception = exception

    def __call__(self, original):
        def wrapper(*args, **kwargs):
            try:
                return original(*args, **kwargs)
            except self.exception:
                raise
            except Exception as e:
                wrapped = self.exception(str(e), e)
                raise wrapped.with_traceback(exc_info()[2]) from e

        wrapper.__name__ = original.__name__
        wrapper.__doc__ = original.__doc__
        wrapper.__dict__.update(original.__dict__)
        return wrapper


class ChainAll:
    """Class decorator that wraps every method to convert exceptions."""

    def __init__(self, exception):
        self.exception = _Chain(exception)

    def __call__(self, cls):
        for method in getmembers(cls, predicate=isfunction):
            setattr(cls, method[0], self.exception(method[1]))
        return cls


def get_stacktrace_info(ex: Exception) -> str:
    return ''.join(format_tb(exc_info()[2]) + [': '.join((ex.__class__.__name__, str(ex)))])


# ---------------------------------------------------------------------------
# Path helpers (equivalent to assemblyline.common.path / assemblyline.common.uid)
# ---------------------------------------------------------------------------

def _get_random_id() -> str:
    return uuid.uuid4().hex


def _splitpath(path: str, sep: Optional[str] = None) -> list:
    """Split the path into a list of items."""
    return list(filter(len, path.split(sep or os.path.sep)))


def _strip_path_inclusion(path: str, base: str) -> str:
    path = path.replace("\\", os.path.sep).replace("/", os.path.sep)
    return path if os.path.abspath(os.path.join(base, path)).startswith(base) else os.path.basename(path)


# ---------------------------------------------------------------------------
# Normalize helper
# ---------------------------------------------------------------------------

def normalize_srl_path(srl):
    if '/' in srl:
        return srl
    return '{0}/{1}/{2}/{3}/{4}'.format(srl[0], srl[1], srl[2], srl[3], srl)


# ---------------------------------------------------------------------------
# Transport base class
# ---------------------------------------------------------------------------

class Transport:
    """
    FileTransport base class.

    Subclasses should override all methods.  Methods raise TransportException
    on failure.
    """

    def __init__(self, normalize=normalize_srl_path, read_only=False):
        self.normalize = normalize
        self.read_only = read_only

    def close(self):
        pass

    def delete(self, path: str):
        """Deletes the file."""
        raise TransportException("Not Implemented")

    def exists(self, path: str) -> bool:
        """Returns True if the path exists, False otherwise."""
        raise TransportException("Not Implemented")

    def makedirs(self, path: str):
        """Like os.makedirs, create the leaf directory and any intermediate path segments."""
        raise TransportException("Not Implemented")

    # File based functions
    def download(self, src_path: str, dst_path: str):
        """Copy the content of the filestore src_path to the local dst_path."""
        raise TransportException("Not Implemented")

    def upload(self, src_path: str, dst_path: str):
        """Save src_path to the filestore dst_path, overwriting if it already exists."""
        raise TransportException("Not Implemented")

    # Buffer based functions
    def get(self, path: str) -> bytes:
        """Return the content of the file."""
        raise TransportException("Not Implemented")

    def put(self, dst_path: str, content: AnyStr):
        """Put the content of a buffer directly to the filestore dst_path."""
        raise TransportException("Not Implemented")

    def list(self, prefix: Optional[str] = None) -> Iterable[str]:
        """List all files in the store filtered by name prefix."""
        raise NotImplementedError()
