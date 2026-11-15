"""Functional tests for the Olog service: Elasticsearch, MongoDB and Olog,
end to end through the REST API."""
import json
import uuid

import pytest

OLOG_URL = "http://localhost:4180/Olog"
OLOG_HTTPS_URL = "https://localhost:4181/Olog"
WEBCLIENT_ORIGIN = "http://localhost:3000"
ADMIN = "admin:adminPass"
USER = "user:userPass"


def curl(host, args):
    result = host.run(f"curl -sS {args}")
    assert result.succeeded, result.stderr
    return result.stdout


def get_json(host, url, auth=None):
    auth_opt = f"-u {auth} " if auth else ""
    return json.loads(curl(host, f"{auth_opt}'{url}'"))


@pytest.fixture(scope="module")
def log_entry(host):
    """Create a log entry with an attachment (multipart, as the clients do)."""
    marker = f"molecule{uuid.uuid4().hex[:8]}"
    entry = {
        "owner": "user",
        "title": f"Molecule test entry {marker}",
        # Olog indexes the description with a whitespace tokenizer (no
        # punctuation stripping) - keep the marker a separate word
        "description": f"Created by the Molecule test: {marker}",
        "level": "Info",
        "logbooks": [{"name": "operations"}],
        "attachments": [{"id": str(uuid.uuid4()), "filename": "molecule.txt"}],
    }
    host.run(f"cat > /tmp/olog_entry.json <<'JSON'\n{json.dumps(entry)}\nJSON")
    host.run(f"printf '%s' '{marker}' > /tmp/molecule.txt")
    created = json.loads(curl(
        host,
        f"-u {USER} -X PUT '{OLOG_URL}/logs/multipart'"
        " -F 'logEntry=@/tmp/olog_entry.json;type=application/json'"
        " -F 'files=@/tmp/molecule.txt;type=text/plain'",
    ))
    assert "id" in created, created
    return {"id": created["id"], "marker": marker}


@pytest.mark.parametrize("service", ["elasticsearch", "mongodb", "olog"])
def test_service_is_running_and_enabled(host, service):
    svc = host.service(service)
    assert svc.is_running
    assert svc.is_enabled


def test_runs_as_unprivileged_user(host):
    assert host.process.filter(user="olog", comm="java")


def test_service_info_reports_backends_connected(host):
    info = get_json(host, OLOG_URL)
    assert info["name"] == "Olog Service"
    assert info["version"].startswith("6.")
    assert info["elastic"]["status"] == "Connected"
    assert info["elastic"]["clusterName"] == "training-vm"
    assert "127.0.0.1:27017" in info["mongoDB"]


def test_https_port_answers(host):
    # Self-signed certificate built into the jar
    info = json.loads(curl(host, f"-k '{OLOG_HTTPS_URL}'"))
    assert info["name"] == "Olog Service"


def test_default_logbooks_created(host):
    names = [lb["name"] for lb in get_json(host, f"{OLOG_URL}/logbooks")]
    assert "operations" in names
    assert "controls" in names


def test_authentication_required_for_writes(host):
    status = curl(
        host,
        f"-o /dev/null -w '%{{http_code}}' -X PUT '{OLOG_URL}/logs'"
        " -H 'Content-Type: application/json' -d '{}'",
    )
    assert status == "401"


def test_built_in_accounts_can_log_in(host):
    for account in (USER, ADMIN):
        name, password = account.split(":")
        reply = json.loads(curl(
            host,
            f"-X POST '{OLOG_URL}/login' -H 'Content-Type: application/json'"
            f" -d '{json.dumps({'username': name, 'password': password})}'",
        ))
        assert reply["userName"] == name


def test_log_entry_is_stored_and_searchable(host, log_entry):
    entry = get_json(host, f"{OLOG_URL}/logs/{log_entry['id']}")
    assert entry["owner"] == "user"
    assert [lb["name"] for lb in entry["logbooks"]] == ["operations"]

    found = get_json(
        host, f"{OLOG_URL}/logs/search?text={log_entry['marker']}"
    )
    assert found["hitCount"] >= 1
    assert log_entry["id"] in [e["id"] for e in found["logs"]]


def test_attachment_is_stored_in_mongodb(host, log_entry):
    content = curl(
        host, f"'{OLOG_URL}/logs/attachments/{log_entry['id']}/molecule.txt'"
    )
    assert content == log_entry["marker"]


def test_cors_allows_the_web_client(host):
    headers = curl(
        host,
        f"-D - -o /dev/null -X OPTIONS '{OLOG_URL}/logs'"
        f" -H 'Origin: {WEBCLIENT_ORIGIN}'"
        " -H 'Access-Control-Request-Method: PUT'",
    ).lower()
    assert f"access-control-allow-origin: {WEBCLIENT_ORIGIN}" in headers
