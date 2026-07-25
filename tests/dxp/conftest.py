"""Shared fixtures for the DxP client tests.

These tests exercise ``custom_components/dataprobe_dxp/dxp.py`` in isolation —
no Home Assistant is imported. A fake socket lets us assert on the exact bytes
sent to the device and feed canned responses back to the client.
"""

from __future__ import annotations

import struct
import sys
from pathlib import Path

import pytest

# Make the vendored client importable as ``dxp``.
_CLIENT_DIR = (
    Path(__file__).resolve().parents[2]
    / "custom_components"
    / "dataprobe_dxp"
)
sys.path.insert(0, str(_CLIENT_DIR))

import dxp  # noqa: E402  pylint: disable=C0413


class FakeSocket:
    """Minimal stand-in for a connected TCP socket.

    Records everything written via ``sendall`` and serves queued bytes from
    ``recv``. ``queue_response`` pre-loads the bytes the device would return.
    """

    def __init__(self) -> None:
        self.sent = bytearray()
        self._recv_buffer = bytearray()
        self.closed = False
        self.timeout = None

    # --- helpers used by tests ---------------------------------------
    def queue_response(self, data: bytes) -> None:
        self._recv_buffer.extend(data)

    def queue_greeting(self, seq: int) -> None:
        """Queue the 2-byte little-endian sequence number handshake."""
        self._recv_buffer.extend(struct.pack("<H", seq))

    # --- socket API used by dxp.py -----------------------------------
    def settimeout(self, timeout) -> None:
        self.timeout = timeout

    def sendall(self, data: bytes) -> None:
        self.sent.extend(data)

    def recv(self, length: int) -> bytes:
        if not self._recv_buffer:
            return b""
        chunk = bytes(self._recv_buffer[:length])
        del self._recv_buffer[:length]
        return chunk

    def close(self) -> None:
        self.closed = True


@pytest.fixture(name="dxp_module")
def fixture_dxp_module():
    """Return the imported dxp module."""
    return dxp


@pytest.fixture(name="fake_socket")
def fixture_fake_socket(monkeypatch):
    """Patch ``dxp.socket.create_connection`` to return a FakeSocket."""
    sock = FakeSocket()

    def _create_connection(address, timeout=None):
        sock.address = address
        sock.connect_timeout = timeout
        return sock

    monkeypatch.setattr(dxp.socket, "create_connection", _create_connection)
    return sock
