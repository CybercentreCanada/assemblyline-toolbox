from __future__ import annotations

import json
import logging
import time
from traceback import format_exception
from typing import TYPE_CHECKING, AnyStr, Optional, Tuple
from urllib.parse import parse_qs, unquote, urlparse

from assemblyline_toolbox.filestore.transport.base import TransportException

if TYPE_CHECKING:
    from assemblyline_toolbox.filestore.transport.base import Transport
    from assemblyline_toolbox.filestore.transport.local import TransportLocal


class FileStoreException(Exception):
    pass


class CorruptedFileStoreException(Exception):
    pass


def _get_extras(parsed_dict, valid_str_keys=None, valid_bool_keys=None):
    if not valid_str_keys:
        valid_str_keys = []
    if not valid_bool_keys:
        valid_bool_keys = []

    out = {}
    for k, v in parsed_dict.items():
        if k in valid_bool_keys:
            if v[0].lower() == 'true':
                out[k] = True
            elif v[0].lower() != 'true':
                out[k] = False
        if k in valid_str_keys:
            out[k] = v[0]

    return out


def create_transport(url, connection_attempts=None):
    """
    Transports are initiated using a URL in the format:
    scheme://user:password@host:port/path/to/file

    Supported schemes: ftp, ftps, sftp, http, https, file, s3, azure.

    Certain transports support extra query-string parameters:
        ftp: use_tls (bool)
        http: pki (string)
        sftp: private_key (string), private_key_pass (string), validate_host (bool)
        s3: aws_region (string), s3_bucket (string), use_ssl (bool), verify (bool)
        file: normalize (bool)
        azure: access_key (string), tenant_id (string), client_id (string), client_secret (string),
               allow_directory_access (bool), use_default_credentials (bool), initalize_container (bool)
    """

    parsed = urlparse(url)

    base = parsed.path or '/'
    host = parsed.hostname
    if host == ".":
        base = "%s%s" % (host, base)
    port = parsed.port
    if parsed.password:
        password = unquote(parsed.password)
    else:
        password = ''
    user = parsed.username or ''

    scheme = parsed.scheme.lower()
    if scheme == 'ftp' or scheme == 'ftps':
        from assemblyline_toolbox.filestore.transport.ftp import TransportFTP
        valid_bool_keys = ['use_tls', 'read_only']
        extras = _get_extras(parse_qs(parsed.query), valid_bool_keys=valid_bool_keys)
        if scheme == 'ftps':
            extras['use_tls'] = True

        t = TransportFTP(base=base, host=host, password=password, user=user, port=port, **extras)

    elif scheme == "sftp":
        from assemblyline_toolbox.filestore.transport.sftp import TransportSFTP
        valid_str_keys = ['private_key', 'private_key_pass']
        valid_bool_keys = ['validate_host', 'read_only']
        extras = _get_extras(parse_qs(parsed.query), valid_str_keys=valid_str_keys, valid_bool_keys=valid_bool_keys)

        t = TransportSFTP(base=base, host=host, password=password, user=user, port=port, **extras)

    elif scheme == 'http' or scheme == 'https':
        from assemblyline_toolbox.filestore.transport.http import TransportHTTP
        valid_str_keys = ['pki']
        valid_bool_keys = ['verify', 'read_only']
        extras = _get_extras(parse_qs(parsed.query), valid_str_keys=valid_str_keys, valid_bool_keys=valid_bool_keys)

        t = TransportHTTP(scheme=scheme, base=base, host=host, password=password, user=user, port=port, **extras)

    elif scheme == 'file':
        from assemblyline_toolbox.filestore.transport.local import TransportLocal
        valid_bool_keys = ['normalize', 'read_only']
        extras = _get_extras(parse_qs(parsed.query), valid_bool_keys=valid_bool_keys)

        t = TransportLocal(base=base, **extras)

    elif scheme == 's3':
        from assemblyline_toolbox.filestore.transport.s3 import TransportS3
        valid_str_keys = ['aws_region', 's3_bucket']
        valid_bool_keys = ['use_ssl', 'verify', 'boto_defaults', 'read_only']
        extras = _get_extras(parse_qs(parsed.query), valid_str_keys=valid_str_keys, valid_bool_keys=valid_bool_keys)

        # If user/password not specified, access might be dictated by IAM roles
        if not user and not password:
            user, password = None, None

        t = TransportS3(base=base, host=host, port=port, accesskey=user, secretkey=password,
                        connection_attempts=connection_attempts, **extras)

    elif scheme == 'azure':
        from assemblyline_toolbox.filestore.transport.azure import TransportAzure
        valid_str_keys = ['access_key', 'tenant_id', 'client_id', 'client_secret']
        valid_bool_keys = ['allow_directory_access', 'use_default_credentials', 'initalize_container', 'read_only']
        extras = _get_extras(parse_qs(parsed.query), valid_str_keys=valid_str_keys, valid_bool_keys=valid_bool_keys)

        t = TransportAzure(base=base, host=host, connection_attempts=connection_attempts, **extras)

    else:
        raise FileStoreException("Unknown transport: %s" % scheme)

    return t


def _get_stacktrace_info(ex: Exception) -> str:
    return ''.join(format_exception(type(ex), ex, ex.__traceback__))


class FileStore(object):
    SLOW_OP_THRESHOLD = 5.0  # Log warning when a single filestore operation exceeds this (seconds)

    def __init__(self, *transport_urls, connection_attempts=None):
        self.log = logging.getLogger('assemblyline.transport')
        self.transport_urls = transport_urls
        self.transports = [create_transport(url, connection_attempts) for url in transport_urls]
        self.local_transports = self._get_local_transports()

    def _get_local_transports(self):
        try:
            from assemblyline_toolbox.filestore.transport.local import TransportLocal
            return [t for t in self.transports if isinstance(t, TransportLocal)]
        except ImportError:
            return []

    def __eq__(self, obj: FileStore) -> bool:
        return self.transport_urls == obj.transport_urls

    def __enter__(self):
        return self

    def __exit__(self, ex_type, exc_val, exc_tb):
        self.close()

    def __str__(self):
        out = ', '.join(str(t) for t in self.transports)
        read_only_transports = [str(t) for t in self.transports if t.read_only]
        if read_only_transports:
            out += " | read-only: {}".format(', '.join(read_only_transports))
        return out

    def close(self):
        for t in self.transports:
            try:
                t.close()
            except Exception as ex:
                self.log.warning('Transport problem: %s', _get_stacktrace_info(ex))

    def delete(self, path: str, location='all'):
        for t in self.slice(location):
            if t.read_only:
                continue

            try:
                t.delete(path)
            except Exception as ex:
                self.log.info('Transport problem: %s', _get_stacktrace_info(ex))

    def download(self, src_path: str, dest_path: str, location='any'):
        successful = False
        transports = []
        download_errors = []
        start = time.monotonic()
        for t in self.slice(location):
            try:
                t.download(src_path, dest_path)
                transports.append(t)
                successful = True
                break
            except Exception as ex:
                download_errors.append((str(t), str(ex)))

        elapsed = time.monotonic() - start
        if elapsed > self.SLOW_OP_THRESHOLD:
            self.log.warning("Slow filestore download: %s took %.2fs (transports tried: %d)",
                             src_path, elapsed, len(download_errors) + len(transports))

        if not successful:
            raise FileStoreException('No transport succeeded => %s' % json.dumps(download_errors))
        return transports

    def exists(self, path, location='any') -> list[Transport]:
        transports = []
        for t in self.slice(location):
            try:
                if t.exists(path):
                    transports.append(t)
                    if location == 'any':
                        break
            except Exception as ex:
                self.log.warning('Transport problem: %s', _get_stacktrace_info(ex))
        return transports

    def get(self, path: str, location='any') -> Optional[bytes]:
        for t in self.slice(location):
            try:
                return t.get(path)
            except TransportException as ex:
                if isinstance(ex.cause, FileNotFoundError):
                    pass
                else:
                    self.log.warning('Transport problem: %s', _get_stacktrace_info(ex))
            except Exception as ex:
                self.log.warning('Transport problem: %s', _get_stacktrace_info(ex))
        return None

    def put(self, dst_path: str, content: AnyStr, location='all', force=False) -> list[Transport]:
        transports = []
        for t in self.slice(location):
            if t.read_only:
                continue

            if force or not t.exists(dst_path):
                transports.append(t)
                t.put(dst_path, content)
                if not t.exists(dst_path):
                    raise FileStoreException('File transfer failed. Remote file does not '
                                             'exist for %s on %s (%s)' % (dst_path, location, t))
        return transports

    def slice(self, location):
        start, end = {
            'all': (0, len(self.transports)),
            'any': (0, len(self.transports)),
            'far': (-1, len(self.transports)),
            'near': (0, 1),
        }[location]

        transports = self.transports[start:end]
        assert (len(transports) >= 1)
        return transports

    def upload(self, src_path: str, dst_path: str, location='all', force=False, verify=False) -> list[Transport]:
        transports = []
        start = time.monotonic()
        for t in self.slice(location):
            if t.read_only:
                continue

            if force or not t.exists(dst_path):
                transports.append(t)
                t.upload(src_path, dst_path)
                if verify and not t.exists(dst_path):
                    raise FileStoreException('File transfer failed. Remote file does not '
                                             'exist for %s on %s (%s)' % (dst_path, location, t))
        elapsed = time.monotonic() - start
        if elapsed > self.SLOW_OP_THRESHOLD:
            self.log.warning("Slow filestore upload: %s took %.2fs across %d transport(s)",
                             dst_path, elapsed, len(transports))
        return transports

    def upload_batch(self, local_remote_tuples, location='all') -> list[Tuple[str, str, str]]:
        failed_tuples = []
        for (src_path, dst_path) in local_remote_tuples:
            try:
                self.upload(src_path, dst_path, location)
            except Exception as ex:
                failed_tuples.append((src_path, dst_path, _get_stacktrace_info(ex)))
        return failed_tuples
