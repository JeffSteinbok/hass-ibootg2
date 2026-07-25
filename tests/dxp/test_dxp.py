"""Unit tests for the vendored Dataprobe DxP client (dxp.py)."""

from __future__ import annotations

import struct

import pytest


HEADER = struct.Struct("<B21s21sBBH")
HEADER_SIZE = HEADER.size  # 47 bytes

CMD_IO = 3
DESC_CHANGE_RELAY = 1
DESC_GET_RELAYS = 4


def _decode_header(frame: bytes):
    command, username, password, descriptor, pad, seq = HEADER.unpack(
        frame[:HEADER_SIZE]
    )
    return {
        "command": command,
        "username": username.rstrip(b"\x00"),
        "password": password.rstrip(b"\x00"),
        "descriptor": descriptor,
        "pad": pad,
        "seq": seq,
        "payload": frame[HEADER_SIZE:],
    }


def _make_client(dxp_module, num_relays=1):
    return dxp_module.DxpClient(
        host="10.0.0.5",
        username="admin",
        password="secret",
        port=9100,
        num_relays=num_relays,
    )


def test_handshake_sends_hello_and_uses_seq(dxp_module, fake_socket):
    """The client greets with hello-000 and derives the seq from the reply."""
    fake_socket.queue_greeting(5)
    fake_socket.queue_response(b"\x00")  # ack for set_relay

    client = _make_client(dxp_module)
    assert client.set_relay(1, True) is True

    # First bytes on the wire are the greeting.
    assert fake_socket.sent.startswith(dxp_module.HELLO)

    # The command frame follows the greeting; seq should be greeting + 1.
    frame = bytes(fake_socket.sent[len(dxp_module.HELLO):])
    header = _decode_header(frame)
    assert header["seq"] == 6


def test_set_relay_on_encoding(dxp_module, fake_socket):
    """set_relay(on=True) encodes an IO/CHANGE_RELAY frame with state 1."""
    fake_socket.queue_greeting(0)
    fake_socket.queue_response(b"\x00")

    client = _make_client(dxp_module)
    client.set_relay(2, True)

    frame = bytes(fake_socket.sent[len(dxp_module.HELLO):])
    header = _decode_header(frame)

    assert header["command"] == CMD_IO
    assert header["descriptor"] == DESC_CHANGE_RELAY
    assert header["username"] == b"admin"
    assert header["password"] == b"secret"
    assert header["pad"] == 0
    # Payload = <relay, state>
    assert header["payload"] == struct.pack("<BB", 2, 1)


def test_set_relay_off_encoding(dxp_module, fake_socket):
    """set_relay(on=False) encodes state 0."""
    fake_socket.queue_greeting(0)
    fake_socket.queue_response(b"\x00")

    client = _make_client(dxp_module)
    client.set_relay(1, False)

    frame = bytes(fake_socket.sent[len(dxp_module.HELLO):])
    header = _decode_header(frame)
    assert header["payload"] == struct.pack("<BB", 1, 0)


def test_set_relay_ack_zero_is_success(dxp_module, fake_socket):
    """A 0x00 ack byte means success; anything else is failure."""
    fake_socket.queue_greeting(0)
    fake_socket.queue_response(b"\x00")
    client = _make_client(dxp_module)
    assert client.set_relay(1, True) is True


def test_set_relay_nonzero_ack_is_failure(dxp_module, fake_socket):
    """A non-zero ack byte is treated as a rejected command."""
    fake_socket.queue_greeting(0)
    fake_socket.queue_response(b"\x01")
    client = _make_client(dxp_module)
    assert client.set_relay(1, True) is False


def test_get_relays_parses_states(dxp_module, fake_socket):
    """get_relays returns one bool per relay byte (1 = on)."""
    fake_socket.queue_greeting(0)
    fake_socket.queue_response(bytes([1, 0, 1, 0]))

    client = _make_client(dxp_module, num_relays=4)
    assert client.get_relays() == [True, False, True, False]

    # Verify it asked for GET_RELAYS with no payload.
    frame = bytes(fake_socket.sent[len(dxp_module.HELLO):])
    header = _decode_header(frame)
    assert header["descriptor"] == DESC_GET_RELAYS
    assert header["payload"] == b""


def test_get_relay_single_index(dxp_module, fake_socket):
    """get_relay returns the state of a single 1-based relay."""
    fake_socket.queue_greeting(0)
    fake_socket.queue_response(bytes([0, 1, 0]))

    client = _make_client(dxp_module, num_relays=3)
    assert client.get_relay(2) is True


def test_get_relay_out_of_range_raises(dxp_module, fake_socket):
    """Requesting a relay the device doesn't report raises DxpError."""
    fake_socket.queue_greeting(0)
    fake_socket.queue_response(bytes([1]))

    client = _make_client(dxp_module, num_relays=1)
    with pytest.raises(dxp_module.DxpError):
        client.get_relay(5)


def test_connection_closed_raises(dxp_module, fake_socket):
    """A short/closed read during handshake surfaces as DxpError."""
    # No greeting queued -> recv returns b"" -> connection closed.
    client = _make_client(dxp_module)
    with pytest.raises(dxp_module.DxpError):
        client.get_relays()


def test_socket_is_closed_after_exchange(dxp_module, fake_socket):
    """Each exchange closes its socket even on success."""
    fake_socket.queue_greeting(0)
    fake_socket.queue_response(b"\x00")
    client = _make_client(dxp_module)
    client.set_relay(1, True)
    assert fake_socket.closed is True


@pytest.mark.parametrize(
    ("response", "expected"),
    [(b"\x00", True), (b"\x01", False), (b"", False)],
)
def test_parse_ack(dxp_module, response, expected):
    """_parse_ack: only a leading 0x00 byte is success."""
    assert dxp_module._parse_ack(response) is expected
