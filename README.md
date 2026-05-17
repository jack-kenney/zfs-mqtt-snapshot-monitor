# ZFS MQTT Snapshot Monitor

Publish `sanoid --monitor-snapshots` results to an MQTT topic as JSON.

This is useful when you already use [sanoid](https://github.com/jimsalterjrs/sanoid) to manage ZFS snapshots and want snapshot health exposed to Home Assistant, Node-RED, Telegraf, or another MQTT consumer.

## Payload

The script publishes a retained JSON payload like this:

```json
{
  "host": "nas01",
  "timestamp": 1779043200,
  "check": "sanoid_monitor_snapshots",
  "status_code": 0,
  "status": "OK",
  "stdout": "...",
  "stderr": ""
}
```

`sanoid --monitor-snapshots` exit codes are mapped as follows:

| Exit code | Status |
| --- | --- |
| `0` | `OK` |
| `1` | `WARNING` |
| `2` | `CRITICAL` |
| `3` | `UNKNOWN` |

## Requirements

- Python 3.8+
- `sanoid`
- `paho-mqtt`

Install the Python dependency:

```sh
python3 -m pip install -r requirements.txt
```

## Configuration

Configuration is provided with environment variables.

| Variable | Required | Default | Description |
| --- | --- | --- | --- |
| `ZFS_MQTT_BROKER` | Yes | | MQTT broker hostname or IP address. |
| `ZFS_MQTT_TOPIC` | Yes | | MQTT topic to publish to. |
| `ZFS_MQTT_PORT` | No | `1883` | MQTT broker port. |
| `ZFS_MQTT_QOS` | No | `1` | MQTT publish QoS. |
| `ZFS_MQTT_RETAIN` | No | `true` | Whether the MQTT message should be retained. |
| `ZFS_MQTT_USERNAME` | No | | MQTT username. |
| `ZFS_MQTT_PASSWORD` | No | | MQTT password. |
| `ZFS_MQTT_CLIENT_ID` | No | `zfs-mqtt-snapshot-monitor-<hostname>` | MQTT client ID. |
| `ZFS_MQTT_TIMEOUT` | No | `60` | Timeout in seconds for the sanoid check. |
| `SANOID_BIN` | No | `/usr/sbin/sanoid` | Path to the sanoid executable. |

## Usage

```sh
export ZFS_MQTT_BROKER="mqtt.example.com"
export ZFS_MQTT_TOPIC="zfs/snapshots/status"
python3 zfs-mqtt-snapshot-monitor.py
```

The script exits with the same status code as `sanoid --monitor-snapshots` after the MQTT payload is published. If configuration is invalid, it exits with `3`.

## Cron Example

Run every 15 minutes:

```cron
*/15 * * * * ZFS_MQTT_BROKER=mqtt.example.com ZFS_MQTT_TOPIC=zfs/snapshots/status /usr/bin/python3 /opt/zfs-mqtt-snapshot-monitor/zfs-mqtt-snapshot-monitor.py
```

## Systemd Timer

Example service:

```ini
[Unit]
Description=Publish ZFS snapshot monitor status to MQTT

[Service]
Type=oneshot
Environment=ZFS_MQTT_BROKER=mqtt.example.com
Environment=ZFS_MQTT_TOPIC=zfs/snapshots/status
ExecStart=/usr/bin/python3 /opt/zfs-mqtt-snapshot-monitor/zfs-mqtt-snapshot-monitor.py
```

Example timer:

```ini
[Unit]
Description=Run ZFS MQTT snapshot monitor every 15 minutes

[Timer]
OnBootSec=5min
OnUnitActiveSec=15min
Unit=zfs-mqtt-snapshot-monitor.service

[Install]
WantedBy=timers.target
```

## License

MIT License. See [LICENSE](LICENSE).
