"""Functional tests for the elasticsearch role."""
import json

ES_URL = "http://127.0.0.1:9200"
TEST_INDEX = "molecule-test"


def es(host, method, path, body=None):
    """Send a request to Elasticsearch, return the decoded JSON reply."""
    cmd = f"curl -sS -X {method} '{ES_URL}{path}'"
    if body is not None:
        cmd += f" -H 'Content-Type: application/json' -d '{json.dumps(body)}'"
    result = host.run(cmd)
    assert result.succeeded, result.stderr
    return json.loads(result.stdout)


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
    service = host.service("elasticsearch")
    assert service.is_running
    assert service.is_enabled


def test_listens_on_localhost_only(host):
    for port in (9200, 9300):
        addresses = listening_addresses(host, port)
        assert addresses, f"nothing listening on port {port}"
        assert all(is_loopback(addr) for addr in addresses), addresses


def test_runs_as_unprivileged_user(host):
    procs = host.process.filter(user="elasticsearch", comm="java")
    assert procs


def test_cluster_is_usable(host):
    health = es(host, "GET", "/_cluster/health")
    assert health["cluster_name"] == "training-vm"
    assert health["status"] in ("green", "yellow")


def test_security_is_disabled(host):
    # No credentials needed - the alarm logger connects without any
    info = es(host, "GET", "/")
    assert info["version"]["number"].startswith("8.")


def test_index_and_search_a_document(host):
    es(host, "DELETE", f"/{TEST_INDEX}")
    created = es(
        host, "PUT", f"/{TEST_INDEX}/_doc/1?refresh=true",
        {"pv": "molecule:test", "severity": "MAJOR"},
    )
    assert created["result"] == "created"

    found = es(
        host, "POST", f"/{TEST_INDEX}/_search",
        {"query": {"match": {"severity": "MAJOR"}}},
    )
    assert found["hits"]["total"]["value"] == 1
    assert found["hits"]["hits"][0]["_source"]["pv"] == "molecule:test"

    assert es(host, "DELETE", f"/{TEST_INDEX}")["acknowledged"]
