import pytest

EPICS_DEV_USER = "epics-dev"
RELEASE_LOCAL_PATH = "/opt/epics/RELEASE.local"


@pytest.mark.parametrize("target", ["EPICS_BASE", "PVXS"])
def test_release_dot_local_is_populated(host, target):
    assert any(
        line.startswith(f"{target}=")
        for line in host.file(RELEASE_LOCAL_PATH).content_string.splitlines()
    )


@pytest.mark.parametrize("executable", ["softIoc", "softIocPVA", "softIocPVX"])
def test_softIocXXX_is_on_path(host, executable):
    with host.sudo(EPICS_DEV_USER):
        cmd = host.run(f"echo exit | bash -lc '{executable}'")
        assert cmd.succeeded
