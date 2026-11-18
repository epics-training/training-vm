import re

import pytest

EPICS_DEV_USER = "epics-dev"
RELEASE_LOCAL_PATH = "/opt/epics/RELEASE.local"
TEST_TOP = "/tmp/iocstats-test"
APP = "statsTest"
IOC_NAME = "MOLTEST"

# Build a minimal IOC application against iocStats, the way a training
# user would: makeBaseApp.pl, RELEASE.local from /opt/epics, then the
# devIocStats dbd and library added to the application Makefile.
BUILD_SCRIPT = f"""\
set -e
rm -rf {TEST_TOP}
mkdir -p {TEST_TOP}
cd {TEST_TOP}
makeBaseApp.pl -t ioc {APP}
cp {RELEASE_LOCAL_PATH} configure/RELEASE.local
sed -i \\
  -e 's|^#{APP}_DBD += xxx.dbd|{APP}_DBD += devIocStats.dbd|' \\
  -e 's|^#{APP}_LIBS += xxx|{APP}_LIBS += devIocStats|' \\
  {APP}App/src/Makefile
grep -q '^{APP}_DBD += devIocStats.dbd' {APP}App/src/Makefile
grep -q '^{APP}_LIBS += devIocStats' {APP}App/src/Makefile
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


def test_release_dot_local_has_iocstats(host):
    assert "IOCSTATS" in release_local(host)


@pytest.mark.parametrize(
    "path",
    [
        "dbd/devIocStats.dbd",
        "db/iocAdminSoft.db",
        "lib/{arch}/libdevIocStats.a",
        "lib/{arch}/libdevIocStats.so",
    ],
)
def test_module_files_are_installed(host, path):
    top = release_local(host)["IOCSTATS"]
    path = path.format(arch=epics_host_arch(host))
    assert host.file(f"{top}/{path}").is_file


@pytest.fixture(scope="module")
def ioc_output(host):
    """Build a test IOC against iocStats, run it once, return its output."""
    with host.sudo(EPICS_DEV_USER):
        host.run_test(f"cat > {TEST_TOP}.sh <<'EOF'\n{BUILD_SCRIPT}EOF")
        build = host.run(f"bash -l {TEST_TOP}.sh")
        assert build.succeeded, build.stdout + build.stderr

        iocstats = release_local(host)["IOCSTATS"]
        st_cmd = "\n".join(
            [
                f"dbLoadDatabase dbd/{APP}.dbd",
                f"{APP}_registerRecordDeviceDriver pdbbase",
                f"dbLoadRecords {iocstats}/db/iocAdminSoft.db"
                f' "IOC={IOC_NAME}"',
                "iocInit",
                f"dbgf {IOC_NAME}:KERNEL_VERS",
                f"dbgf {IOC_NAME}:PROCESS_ID",
                "",
            ]
        )
        host.run_test(f"cat > {TEST_TOP}/st.cmd <<'EOF'\n{st_cmd}EOF")
        run = host.run(
            f"cd {TEST_TOP} && echo exit | "
            f"bin/{epics_host_arch(host)}/{APP} st.cmd"
        )
        assert run.succeeded, run.stdout + run.stderr
        return run.stdout


def test_ioc_reports_kernel_version(host, ioc_output):
    # stringin device support: "<sysname> <release> <machine>" from uname(),
    # truncated to the 40 character stringin value
    expected = f"Linux {host.check_output('uname -r')}"[:39]
    match = re.search(r'DBF_STRING:\s+"([^"]*)"', ioc_output)
    assert match, ioc_output
    assert match.group(1).startswith(expected)


def test_ioc_reports_process_id(host, ioc_output):
    # ai device support (devIocStatsAnalog.c, the GCC >= 14 workaround)
    match = re.search(r"DBF_DOUBLE:\s+([0-9.eE+-]+)", ioc_output)
    assert match, ioc_output
    assert float(match.group(1)) > 0
