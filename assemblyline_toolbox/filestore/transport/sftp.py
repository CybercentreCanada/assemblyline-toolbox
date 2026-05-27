from __future__ import annotations

import logging
import os
import posixpath
import tempfile
import warnings

from io import BytesIO
from typing import Optional

from .base import (
    ChainAll,
    Transport,
    TransportException,
    _get_random_id,
    normalize_srl_path,
)


def reconnect_retry_on_fail(func):
    def new_func(self, *args, **kwargs):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")

            try:
                if not self.sftp:
                    self.sftp = self._connect()
                return func(self, *args, **kwargs)
            except Exception:
                pass

            # The previous attempt at calling original func failed.
            # Reset the connection and try again (one time).
            if self.sftp:
                try:
                    self.sftp.close()
                except Exception:
                    pass

            self.sftp = self._connect()
            return func(self, *args, **kwargs)

    new_func.__name__ = func.__name__
    new_func.__doc__ = func.__doc__
    return new_func


@ChainAll(TransportException)
class TransportSFTP(Transport):
    """SFTP Transport class."""

    def __init__(self, base=None, host=None, password=None, user=None, port=None, private_key=None,
                 private_key_pass=None, validate_host=False, read_only=False):
        self.log = logging.getLogger('assemblyline.transport.sftp')
        if base == "/":
            self.base = "./"
        else:
            self.base = base
        self.host = host
        self.port = int(port or 22)
        self.password = password
        self.user = user
        self.private_key = private_key
        self.private_key_pass = private_key_pass
        self.validate_host = validate_host

        # Connect on create
        self.sftp = self._connect()

        def sftp_normalize(path):
            if path.startswith('/'):
                s = path
            elif '/' in path or len(path) != 64:
                s = posixpath.join(self.base, path)
            else:
                s = posixpath.join(self.base, normalize_srl_path(path))
            self.log.debug('sftp normalized: %s -> %s', path, s)
            return s

        super(TransportSFTP, self).__init__(normalize=sftp_normalize, read_only=read_only)

    def _connect(self):
        import pysftp
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            if not self.validate_host:
                cnopts = pysftp.CnOpts()
                cnopts.hostkeys = None
            else:
                cnopts = None
            return pysftp.Connection(self.host,
                                     username=self.user,
                                     password=self.password,
                                     private_key=self.private_key,
                                     private_key_pass=self.private_key_pass,
                                     port=self.port,
                                     cnopts=cnopts)

    def __str__(self):
        return 'sftp://{}@{}{}'.format(self.user, self.host, self.base)

    def close(self):
        if self.sftp:
            self.sftp.close()

    @reconnect_retry_on_fail
    def delete(self, path):
        path = self.normalize(path)
        self.sftp.remove(path)

    @reconnect_retry_on_fail
    def exists(self, path):
        path = self.normalize(path)
        return self.sftp.exists(path)

    @reconnect_retry_on_fail
    def makedirs(self, path):
        path = self.normalize(path)
        self.sftp.makedirs(path)

    # File based functions
    @reconnect_retry_on_fail
    def download(self, src_path, dst_path):
        dir_path = os.path.dirname(dst_path)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
        src_path = self.normalize(src_path)
        self.sftp.get(src_path, dst_path)

    @reconnect_retry_on_fail
    def upload(self, src_path, dst_path):
        dst_path = self.normalize(dst_path)
        dirname = posixpath.dirname(dst_path)
        filename = posixpath.basename(dst_path)
        tempname = _get_random_id()
        temppath = posixpath.join(dirname, tempname)
        finalpath = posixpath.join(dirname, filename)
        assert (finalpath == dst_path)
        self.makedirs(dirname)
        self.sftp.put(src_path, temppath)
        self.sftp.rename(temppath, finalpath)
        assert (self.exists(dst_path))

    # Buffer based functions
    @reconnect_retry_on_fail
    def get(self, path: str) -> bytes:
        path = self.normalize(path)
        bio = BytesIO()
        with self.sftp.open(path) as sftp_handle:
            bio.write(sftp_handle.read())
        return bio.getvalue()

    @reconnect_retry_on_fail
    def put(self, dst_path, content):
        dst_path = self.normalize(dst_path)
        dirname = posixpath.dirname(dst_path)
        filename = posixpath.basename(dst_path)
        tempname = _get_random_id()
        temppath = posixpath.join(dirname, tempname)
        finalpath = posixpath.join(dirname, filename)
        assert (finalpath == dst_path)

        if isinstance(content, str):
            content_data = content.encode('utf-8')
        else:
            content_data = content

        fd, src_path = tempfile.mkstemp(prefix="filestore.local_path")
        with open(fd, "wb") as f:
            f.write(content_data)

        self.makedirs(dirname)
        self.sftp.put(src_path, temppath)
        self.sftp.rename(temppath, finalpath)
        assert (self.exists(dst_path))

        os.unlink(src_path)
