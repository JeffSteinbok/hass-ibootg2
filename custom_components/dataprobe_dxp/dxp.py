"""Minimal client for the Dataprobe DxP protocol (iBoot / iBoot-G2 / iBoot Bar).

The DxP protocol is a small binary protocol spoken over a raw TCP socket
(default port 9100). This module implements just enough of it to read and
change relay (outlet) state.

Protocol summary
----------------
1. Open a TCP connection to the device.
2. Send the literal greeting ``hello-000``.
3. The device replies with a 2-byte little-endian sequence number.
4. Every request is a header followed by an optional payload::

       header = <command:1><username:21s><password:21s><descriptor:1><pad:1><seq:2>

5. The sequence number is incremented after each exchange.
"""

from __future__ import annotations

import logging
import socket
import struct

_LOGGER = logging.getLogger(__name__)

HELLO = b"hello-000"
DEFAULT_PORT = 9100
SOCKET_TIMEOUT = 10

# Command header: command, username(21), password(21), descriptor, pad, seq.
_HEADER = struct.Struct("<B21s21sBBH")
# Change-relay payload: relay number, requested state.
_CHANGE_RELAY = struct.Struct("<BB")

_CMD_IO = 3

_DESC_CHANGE_RELAY = 1
_DESC_GET_RELAYS = 4

_STATE_OFF = 0
_STATE_ON = 1


class DxpError(Exception):
    """Raised when communication with the device fails."""


class DxpClient:
    """Blocking client for a Dataprobe DxP device.

    Every method opens a fresh connection, performs a single logical operation
    and closes it again. This keeps the client stateless and robust, which is
    what the iBoot firmware expects between commands. The blocking calls are
    intended to be run inside an executor by the Home Assistant integration.
    """

    def __init__(
        self,
        host: str,
        username: str,
        password: str,
        port: int = DEFAULT_PORT,
        num_relays: int = 1,
    ) -> None:
        self._host = host
        self._port = port
        self._username = username.encode("ascii")
        self._password = password.encode("ascii")
        self._num_relays = num_relays

    @property
    def num_relays(self) -> int:
        """Number of relays this client expects to read from the device."""
        return self._num_relays

    def set_relay(self, relay: int, on: bool) -> bool:
        """Turn a relay on or off. Return ``True`` on success."""
        with _Connection(self._host, self._port) as conn:
            header = self._build_header(conn.next_seq(), _DESC_CHANGE_RELAY)
            payload = _CHANGE_RELAY.pack(relay, _STATE_ON if on else _STATE_OFF)
            conn.send(header + payload)
            return _parse_ack(conn.recv(1))

    def get_relays(self) -> list[bool]:
        """Return the on/off state of every relay on the device."""
        with _Connection(self._host, self._port) as conn:
            header = self._build_header(conn.next_seq(), _DESC_GET_RELAYS)
            conn.send(header)
            response = conn.recv(self._num_relays)
            return [byte == 1 for byte in response]

    def get_relay(self, relay: int) -> bool:
        """Return the state of a single (1-indexed) relay."""
        relays = self.get_relays()
        index = relay - 1
        if index < 0 or index >= len(relays):
            raise DxpError(
                f"Relay {relay} out of range (device reports "
                f"{len(relays)} relays)"
            )
        return relays[index]

    def _build_header(self, seq: int, descriptor: int) -> bytes:
        return _HEADER.pack(
            _CMD_IO,
            self._username,
            self._password,
            descriptor,
            0,
            seq,
        )


class _Connection:
    """Context manager wrapping a single DxP TCP exchange."""

    def __init__(self, host: str, port: int) -> None:
        self._host = host
        self._port = port
        self._socket: socket.socket | None = None
        self._seq = 0

    def __enter__(self) -> "_Connection":
        try:
            self._socket = socket.create_connection(
                (self._host, self._port), timeout=SOCKET_TIMEOUT
            )
            self._socket.settimeout(SOCKET_TIMEOUT)
            self._socket.sendall(HELLO)
            greeting = self._recv_exact(2)
            self._seq = struct.unpack("<H", greeting)[0] + 1
        except OSError as err:
            self.__exit__(None, None, None)
            raise DxpError(f"Failed to connect to {self._host}: {err}") from err
        return self

    def __exit__(self, *_exc) -> None:
        if self._socket is not None:
            try:
                self._socket.close()
            finally:
                self._socket = None

    def next_seq(self) -> int:
        seq = self._seq
        self._seq += 1
        return seq

    def send(self, data: bytes) -> None:
        assert self._socket is not None
        try:
            self._socket.sendall(data)
        except OSError as err:
            raise DxpError(f"Failed to send command: {err}") from err

    def recv(self, length: int) -> bytes:
        return self._recv_exact(length)

    def _recv_exact(self, length: int) -> bytes:
        assert self._socket is not None
        chunks = bytearray()
        while len(chunks) < length:
            try:
                chunk = self._socket.recv(length - len(chunks))
            except OSError as err:
                raise DxpError(f"Failed to read response: {err}") from err
            if not chunk:
                raise DxpError("Connection closed by device")
            chunks.extend(chunk)
        return bytes(chunks)


def _parse_ack(response: bytes) -> bool:
    """A single ``0x00`` byte means the command was accepted."""
    if not response:
        return False
    return response[0] == 0
