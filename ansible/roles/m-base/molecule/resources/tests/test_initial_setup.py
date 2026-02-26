import pytest

EPICS_DEV_USER = "epics-dev"


@pytest.mark.parametrize("executable", ["softIoc", "softIocPVA", "softIocPVX"])
def test_softIocXXX_is_on_path(host, executable):
    with host.sudo(EPICS_DEV_USER):
        cmd = host.run(f"echo exit | bash -lc '{executable}'")
        assert cmd.succeeded
