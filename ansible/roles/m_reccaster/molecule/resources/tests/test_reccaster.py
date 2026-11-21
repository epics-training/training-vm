import re

import pytest

EPICS_DEV_USER = "epics-dev"
RELEASE_LOCAL_PATH = "/opt/epics/RELEASE.local"
TEST_TOP = "/tmp/reccaster-test"
APP = "castTest"
IOC_NAME = "MOLTEST"

# Build an IOC against reccaster, as a training user would
BUILD_SCRIPT = f"""\
set -e
rm -rf {TEST_TOP}
mkdir -p {TEST_TOP}
cd {TEST_TOP}
makeBaseApp.pl -t ioc {APP}
cp {RELEASE_LOCAL_PATH} configure/RELEASE.local
sed -i \\
  -e 's|^#{APP}_DBD += xxx.dbd|{APP}_DBD += reccaster.dbd|' \\
  -e 's|^#{APP}_LIBS += xxx|{APP}_LIBS += reccaster|' \\
  {APP}App/src/Makefile
grep -q '^{APP}_DBD += reccaster.dbd' {APP}App/src/Makefile
grep -q '^{APP}_LIBS += reccaster' {APP}App/src/Makefile
make
"""


def epics_host_arch(host):
    return f"linux-{host.system_info.arch}"


def release_local(host):
    entries = {}
    for line in host.file(RELEASE_LOCAL_PATH).content_string.splitlines():
        key, sep, value = line.partition("=")
        if sep:
            entries[key.strip()] = value.strip()
    return entries


def test_release_dot_local_has_reccaster(host):
    # The module is recsync's client/ directory
    assert release_local(host)["RECCASTER"].endswith("/client")


@pytest.mark.parametrize(
    "path",
    [
        "dbd/reccaster.dbd",
        "db/reccaster.db",
        "lib/{arch}/libreccaster.a",
        "lib/{arch}/libreccaster.so",
    ],
)
def test_module_files_are_installed(host, path):
    top = release_local(host)["RECCASTER"]
    path = path.format(arch=epics_host_arch(host))
    assert host.file(f"{top}/{path}").is_file


def test_demo_ioc_is_not_built(host):
    top = release_local(host)["RECCASTER"]
    assert not host.file(f"{top}/bin/{epics_host_arch(host)}/demo").exists


@pytest.fixture(scope="module")
def ioc_output(host):
    """Build a test IOC against reccaster, run it briefly, return output."""
    with host.sudo(EPICS_DEV_USER):
        host.run_test(f"cat > {TEST_TOP}.sh <<'EOF'\n{BUILD_SCRIPT}EOF")
        build = host.run(f"bash -l {TEST_TOP}.sh")
        assert build.succeeded, build.stdout + build.stderr

        reccaster = release_local(host)["RECCASTER"]
        st_cmd = "\n".join(
            [
                f"dbLoadDatabase dbd/{APP}.dbd",
                f"{APP}_registerRecordDeviceDriver pdbbase",
                'epicsEnvSet("BUILDING", "molecule")',
                'addReccasterEnvVars("BUILDING")',
                'addReccasterExcludePattern("*:Hidden")',
                f"dbLoadRecords {reccaster}/db/reccaster.db"
                f' "P={IOC_NAME}:"',
                "iocInit",
                # Let the caster thread start listening
                "epicsThreadSleep 3",
                f"dbgf {IOC_NAME}:State-Sts",
                f"dbgf {IOC_NAME}:Msg-I",
                "",
            ]
        )
        host.run_test(f"cat > {TEST_TOP}/st.cmd <<'EOF'\n{st_cmd}EOF")
        run = host.run(
            f"cd {TEST_TOP} && echo exit | "
            f"bin/{epics_host_arch(host)}/{APP} st.cmd"
        )
        assert run.succeeded, run.stdout + run.stderr
        return run.stdout + run.stderr


def test_ioc_accepts_reccaster_iocsh_commands(host, ioc_output):
    # Unknown commands and bad arguments are reported, not fatal
    assert "Command addReccasterEnvVars not found" not in ioc_output
    assert "Command addReccasterExcludePattern not found" not in ioc_output
    assert "sevr=" not in ioc_output, ioc_output


def test_caster_waits_for_a_recceiver(host, ioc_output):
    # No recceiver here (see the recceiver scenario): State-Sts, then Msg-I
    values = re.findall(r'DBF_STRING:\s+"([^"]*)"', ioc_output)
    assert values == ["Listening", "Searching"], ioc_output
