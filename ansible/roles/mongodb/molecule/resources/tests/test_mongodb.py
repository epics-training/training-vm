"""Functional tests for the mongodb role."""

MONGOD = "/opt/epics-tools/services/mongodb/release/bin/mongod"

# There is no MongoDB shell in the server release (and no pymongo in the
# container), so this tiny client speaks the wire protocol itself:
# one OP_MSG with the "hello" command, printing the reply document's raw bytes.
HELLO_CLIENT = r"""
import socket, struct, sys

def bson(*elements):
    body = b"".join(elements) + b"\x00"
    return struct.pack("<i", len(body) + 4) + body

def int32(name, value):
    return b"\x10" + name.encode() + b"\x00" + struct.pack("<i", value)

def string(name, value):
    data = value.encode() + b"\x00"
    size = struct.pack("<i", len(data))
    return b"\x02" + name.encode() + b"\x00" + size + data

doc = bson(int32("hello", 1), string("$db", "admin"))
payload = struct.pack("<I", 0) + b"\x00" + doc
header = struct.pack("<iiii", 16 + len(payload), 1, 0, 2013)

sock = socket.create_connection(("127.0.0.1", 27017), timeout=10)
sock.sendall(header + payload)

def recv(n):
    data = b""
    while len(data) < n:
        chunk = sock.recv(n - len(data))
        if not chunk:
            sys.exit("connection closed")
        data += chunk
    return data

length, _, _, opcode = struct.unpack("<iiii", recv(16))
reply = recv(length - 16)
assert opcode == 2013, opcode
sys.stdout.write(reply[5:].hex())
"""


def listening_addresses(host, port):
    """Local addresses (without %interface) with a TCP listener on the port."""
    return [
        spec.split("://", 1)[1].rsplit(":", 1)[0].split("%", 1)[0]
        for spec in host.socket.get_listening_sockets()
        if spec.startswith("tcp") and spec.endswith(f":{port}")
    ]


def is_loopback(address):
    return address.startswith("127.") or address in ("::1", "::ffff:127.0.0.1")


def test_service_is_running_and_enabled(host):
    service = host.service("mongodb")
    assert service.is_running
    assert service.is_enabled


def test_listens_on_localhost_only(host):
    addresses = listening_addresses(host, 27017)
    assert addresses, "nothing listening on port 27017"
    assert all(is_loopback(addr) for addr in addresses), addresses


def test_runs_as_unprivileged_user(host):
    assert host.process.filter(user="mongodb", comm="mongod")


def test_server_version(host):
    result = host.run(f"{MONGOD} --version")
    assert result.succeeded, result.stderr
    assert "db version v8.0." in result.stdout


def test_answers_hello_command(host):
    result = host.run(f"python3 -c '{HELLO_CLIENT}'")
    assert result.succeeded, result.stderr
    reply = bytes.fromhex(result.stdout)
    # A standalone server is a writable primary, and the command succeeded
    assert b"\x08isWritablePrimary\x00\x01" in reply
    assert b"\x01ok\x00\x00\x00\x00\x00\x00\x00\xf0\x3f" in reply
