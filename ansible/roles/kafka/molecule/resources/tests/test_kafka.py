"""Functional tests for the kafka role."""
import uuid

KAFKA_BIN = "/opt/epics-tools/lib/kafka/bin"
BOOTSTRAP = "localhost:9092"
# The java role installs a single JDK (and removes older ones)
JAVA_ENV = "JAVA_HOME=$(ls -d /opt/epics-tools/lib/jvm/jdk-* | tail -n 1)"


def kafka(host, tool, args, stdin=None):
    """Run a Kafka command line tool, return the result."""
    cmd = f"{JAVA_ENV} {KAFKA_BIN}/{tool} --bootstrap-server {BOOTSTRAP}"
    cmd += f" {args}"
    if stdin is not None:
        cmd = f"echo '{stdin}' | {cmd}"
    return host.run(cmd)


def test_service_is_running_and_enabled(host):
    service = host.service("kafka")
    assert service.is_running
    assert service.is_enabled


def listening_addresses(host, port):
    """Local addresses (without %interface) with a TCP listener on the port."""
    return [
        spec.split("://", 1)[1].rsplit(":", 1)[0].split("%", 1)[0]
        for spec in host.socket.get_listening_sockets()
        if spec.startswith("tcp") and spec.endswith(f":{port}")
    ]


def is_loopback(address):
    return address.startswith("127.") or address in ("::1", "::ffff:127.0.0.1")


def test_listens_on_localhost_only(host):
    # 'localhost' may resolve to an IPv4, IPv6 or IPv4-mapped address
    for port in (9092, 9093):
        addresses = listening_addresses(host, port)
        assert addresses, f"nothing listening on port {port}"
        assert all(is_loopback(addr) for addr in addresses), addresses


def test_runs_as_unprivileged_user(host):
    assert host.process.filter(user="kafka", comm="java")


def test_tools_are_on_the_path(host):
    cmd = host.run("bash -lc 'command -v kafka-topics.sh'")
    assert cmd.succeeded
    assert cmd.stdout.strip() == f"{KAFKA_BIN}/kafka-topics.sh"


def test_produce_and_consume_a_message(host):
    topic = "molecule-test"
    message = f"hello-{uuid.uuid4()}"

    kafka(host, "kafka-topics.sh", f"--delete --if-exists --topic {topic}")
    created = kafka(
        host, "kafka-topics.sh",
        f"--create --topic {topic} --partitions 1 --replication-factor 1",
    )
    assert created.succeeded, created.stderr

    produced = kafka(
        host, "kafka-console-producer.sh", f"--topic {topic}", stdin=message
    )
    assert produced.succeeded, produced.stderr

    consumed = kafka(
        host, "kafka-console-consumer.sh",
        f"--topic {topic} --from-beginning"
        " --max-messages 1 --timeout-ms 30000",
    )
    assert consumed.succeeded, consumed.stderr
    assert message in consumed.stdout

    kafka(host, "kafka-topics.sh", f"--delete --topic {topic}")


def test_topics_are_not_created_automatically(host):
    # The alarm server creates its topics on purpose with the right settings
    props = host.file("/opt/epics-tools/config/kafka/server.properties")
    assert props.contains("^auto.create.topics.enable=false")
