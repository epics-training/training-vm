"""Functional tests for the Olog web client (and the Olog service behind it).
"""
import json

import pytest

WEBCLIENT_URL = "http://localhost:3000"
OLOG_URL = "http://localhost:4180/Olog"
BUILD_DIR = "/opt/epics-tools/lib/phoebus-olog-web-client/build"


def curl(host, args):
    result = host.run(f"curl -sS {args}")
    assert result.succeeded, result.stderr
    return result.stdout


@pytest.mark.parametrize(
    "service", ["elasticsearch", "mongodb", "olog", "olog-webclient"]
)
def test_service_is_running_and_enabled(host, service):
    svc = host.service(service)
    assert svc.is_running
    assert svc.is_enabled


def test_runs_as_unprivileged_user(host):
    assert host.process.filter(user="olog-webclient", comm="node")


def test_serves_the_application(host):
    page = curl(host, f"'{WEBCLIENT_URL}/'")
    assert '<div id="root">' in page
    # The built page, not the development one
    assert "/src/index.jsx" not in page


def test_single_page_routes_are_served(host):
    # Client-side routes (e.g. a log entry) fall back to index.html
    page = curl(host, f"'{WEBCLIENT_URL}/logs/1'")
    assert '<div id="root">' in page


def test_build_points_at_the_olog_service(host):
    result = host.run(f"grep -rl '{OLOG_URL}' {BUILD_DIR}/assets")
    assert result.succeeded, "Olog URL not found in the built assets"
    # No placeholder left over from .env.production
    result = host.run(f"grep -rl 'VITE_APP_BACKEND_URL' {BUILD_DIR}/assets")
    assert not result.succeeded, result.stdout


def test_browser_can_reach_olog(host):
    # What the browser does: a CORS request from the web client's origin
    headers = curl(
        host,
        f"-D - -o /dev/null '{OLOG_URL}/logbooks'"
        f" -H 'Origin: {WEBCLIENT_URL}'",
    ).lower()
    assert f"access-control-allow-origin: {WEBCLIENT_URL}" in headers


def test_login_from_the_web_client(host):
    headers = curl(
        host,
        f"-D - -o /dev/null -X POST '{OLOG_URL}/login'"
        f" -H 'Origin: {WEBCLIENT_URL}' -H 'Content-Type: application/json'"
        f" -d '{json.dumps({'username': 'user', 'password': 'userPass'})}'",
    ).lower()
    assert "set-cookie: session=" in headers
    assert f"access-control-allow-origin: {WEBCLIENT_URL}" in headers
