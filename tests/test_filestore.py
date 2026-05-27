from __future__ import annotations

import os
import tempfile

import pytest

from assemblyline_toolbox.filestore import FileStore, FileStoreException, create_transport
from assemblyline_toolbox.filestore.transport.base import TransportException
from assemblyline_toolbox.filestore.transport.local import TransportLocal


@pytest.fixture
def tmp_store(tmp_path):
    """Create a temporary local FileStore."""
    store = FileStore("file://" + str(tmp_path))
    yield store
    store.close()


class TestTransportLocal:
    def test_put_and_get(self, tmp_path):
        t = TransportLocal(base=str(tmp_path))
        t.put("hello.txt", b"hello world")
        assert t.get("hello.txt") == b"hello world"

    def test_put_string_content(self, tmp_path):
        t = TransportLocal(base=str(tmp_path))
        t.put("test.txt", "utf8 content")
        assert t.get("test.txt") == b"utf8 content"

    def test_exists(self, tmp_path):
        t = TransportLocal(base=str(tmp_path))
        assert not t.exists("missing.txt")
        t.put("exists.txt", b"data")
        assert t.exists("exists.txt")

    def test_delete(self, tmp_path):
        t = TransportLocal(base=str(tmp_path))
        t.put("todelete.txt", b"data")
        assert t.exists("todelete.txt")
        t.delete("todelete.txt")
        assert not t.exists("todelete.txt")

    def test_delete_missing(self, tmp_path):
        """Deleting a non-existent file should not raise."""
        t = TransportLocal(base=str(tmp_path))
        t.delete("ghost.txt")

    def test_upload_and_download(self, tmp_path):
        src = tmp_path / "src.txt"
        src.write_bytes(b"upload test")
        dst_dir = tmp_path / "store"
        dst_dir.mkdir()
        t = TransportLocal(base=str(dst_dir))

        t.upload(str(src), "uploaded.txt")
        assert t.exists("uploaded.txt")

        download_path = str(tmp_path / "downloaded.txt")
        t.download("uploaded.txt", download_path)
        assert open(download_path, "rb").read() == b"upload test"

    def test_list(self, tmp_path):
        t = TransportLocal(base=str(tmp_path))
        t.put("a.txt", b"a")
        t.put("b.txt", b"b")
        files = list(t.list())
        assert "a.txt" in files
        assert "b.txt" in files

    def test_list_prefix(self, tmp_path):
        t = TransportLocal(base=str(tmp_path))
        t.put("alpha.txt", b"a")
        t.put("beta.txt", b"b")
        files = list(t.list(prefix="al"))
        assert "alpha.txt" in files
        assert "beta.txt" not in files

    def test_str(self, tmp_path):
        t = TransportLocal(base=str(tmp_path))
        assert str(t) == "file://" + str(tmp_path)

    def test_read_only(self, tmp_path):
        t = TransportLocal(base=str(tmp_path), read_only=True)
        assert t.read_only is True


class TestFileStore:
    def test_put_get(self, tmp_store):
        tmp_store.put("file.txt", b"content")
        assert tmp_store.get("file.txt") == b"content"

    def test_get_missing(self, tmp_store):
        assert tmp_store.get("missing.txt") is None

    def test_exists(self, tmp_store):
        assert tmp_store.exists("nope.txt") == []
        tmp_store.put("yep.txt", b"data")
        assert len(tmp_store.exists("yep.txt")) == 1

    def test_delete(self, tmp_store):
        tmp_store.put("del.txt", b"x")
        tmp_store.delete("del.txt")
        assert tmp_store.get("del.txt") is None

    def test_upload_download(self, tmp_path):
        src = tmp_path / "src.bin"
        src.write_bytes(b"binary data")
        store_dir = tmp_path / "store"
        store_dir.mkdir()

        store = FileStore("file://" + str(store_dir))
        store.upload(str(src), "stored.bin")
        assert store.get("stored.bin") == b"binary data"

        dest = str(tmp_path / "dest.bin")
        store.download("stored.bin", dest)
        assert open(dest, "rb").read() == b"binary data"
        store.close()

    def test_context_manager(self, tmp_path):
        with FileStore("file://" + str(tmp_path)) as store:
            store.put("ctx.txt", b"ctx")
            assert store.get("ctx.txt") == b"ctx"

    def test_upload_batch(self, tmp_path):
        files = []
        store_dir = tmp_path / "store"
        store_dir.mkdir()
        for i in range(3):
            f = tmp_path / f"file{i}.txt"
            f.write_bytes(f"content{i}".encode())
            files.append((str(f), f"file{i}.txt"))

        store = FileStore("file://" + str(store_dir))
        failures = store.upload_batch(files)
        assert failures == []
        for i in range(3):
            assert store.get(f"file{i}.txt") == f"content{i}".encode()
        store.close()

    def test_str(self, tmp_path):
        store = FileStore("file://" + str(tmp_path))
        assert "file://" in str(store)
        store.close()

    def test_equality(self, tmp_path):
        url = "file://" + str(tmp_path)
        assert FileStore(url) == FileStore(url)

    def test_put_force(self, tmp_store):
        tmp_store.put("force.txt", b"v1")
        tmp_store.put("force.txt", b"v2", force=True)
        assert tmp_store.get("force.txt") == b"v2"

    def test_slice_near(self, tmp_path):
        store_dir = tmp_path / "store"
        store_dir.mkdir()
        store = FileStore("file://" + str(store_dir))
        transports = store.slice("near")
        assert len(transports) == 1
        store.close()


class TestCreateTransport:
    def test_file_scheme(self, tmp_path):
        t = create_transport("file://" + str(tmp_path))
        assert isinstance(t, TransportLocal)
        assert t.base == str(tmp_path)

    def test_unknown_scheme(self):
        with pytest.raises(FileStoreException, match="Unknown transport"):
            create_transport("unknown://host/path")
