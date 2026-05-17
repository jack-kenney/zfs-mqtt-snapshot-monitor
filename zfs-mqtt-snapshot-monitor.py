#!/usr/bin/env python3
"""Publish sanoid snapshot monitoring results to MQTT."""

import json
import os
import socket
import subprocess
import sys
import time

import paho.mqtt.client as mqtt

DEFAULT_SANOID_BIN = "/usr/sbin/sanoid"
DEFAULT_TIMEOUT_SECONDS = 60
DEFAULT_MQTT_PORT = 1883
DEFAULT_QOS = 1

STATUS_MAP = {
    0: "OK",
    1: "WARNING",
    2: "CRITICAL",
    3: "UNKNOWN",
}


def get_required_env(name):
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def get_int_env(name, default):
    value = os.getenv(name)
    if value is None:
        return default

    try:
        return int(value)
    except ValueError as exc:
        raise RuntimeError(f"{name} must be an integer") from exc


def get_bool_env(name, default):
    value = os.getenv(name)
    if value is None:
        return default

    return value.strip().lower() in {"1", "true", "yes", "on"}


def run_sanoid():
    sanoid_bin = os.getenv("SANOID_BIN", DEFAULT_SANOID_BIN)
    timeout = get_int_env("ZFS_MQTT_TIMEOUT", DEFAULT_TIMEOUT_SECONDS)

    try:
        result = subprocess.run(
            [sanoid_bin, "--monitor-snapshots"],
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except FileNotFoundError:
        return 3, "", f"sanoid executable not found: {sanoid_bin}"
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout or ""
        stderr = exc.stderr or ""
        return 3, stdout, f"sanoid timed out after {timeout} seconds\n{stderr}".strip()

    return result.returncode, result.stdout, result.stderr


def publish_payload(payload):
    broker = get_required_env("ZFS_MQTT_BROKER")
    topic = get_required_env("ZFS_MQTT_TOPIC")
    port = get_int_env("ZFS_MQTT_PORT", DEFAULT_MQTT_PORT)
    qos = get_int_env("ZFS_MQTT_QOS", DEFAULT_QOS)
    retain = get_bool_env("ZFS_MQTT_RETAIN", True)
    username = os.getenv("ZFS_MQTT_USERNAME")
    password = os.getenv("ZFS_MQTT_PASSWORD")
    client_id = os.getenv(
        "ZFS_MQTT_CLIENT_ID",
        f"zfs-mqtt-snapshot-monitor-{socket.gethostname()}",
    )

    client = mqtt.Client(client_id=client_id)
    if username:
        client.username_pw_set(username, password)

    client.connect(broker, port, 60)
    publish_result = client.publish(topic, json.dumps(payload), qos=qos, retain=retain)
    publish_result.wait_for_publish()
    client.disconnect()


def main():
    status_code, stdout, stderr = run_sanoid()

    payload = {
        "host": socket.gethostname(),
        "timestamp": int(time.time()),
        "check": "sanoid_monitor_snapshots",
        "status_code": status_code,
        "status": STATUS_MAP.get(status_code, "UNKNOWN"),
        "stdout": stdout.strip(),
        "stderr": stderr.strip(),
    }

    publish_payload(payload)
    return status_code


if __name__ == "__main__":
    try:
        sys.exit(main())
    except RuntimeError as exc:
        print(exc, file=sys.stderr)
        sys.exit(3)
