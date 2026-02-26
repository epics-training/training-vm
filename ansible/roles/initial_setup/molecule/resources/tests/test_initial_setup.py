EPICS_DEV_USER = "epics-dev"


def test_development_user_exists(host):
    assert host.user(EPICS_DEV_USER).exists


def test_development_user_has_sudo_permissions(host):
    assert host.file("/etc/sudoers").contains(
        f"%{EPICS_DEV_USER} ALL=(ALL) NOPASSWD: ALL"
    )


def test_python_is_python3(host):
    cmd = host.run("python --version")
    assert cmd.succeeded

    # Output is "Python <version>"
    assert cmd.stdout.split()[-1].startswith("3.")
