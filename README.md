# Prometheus Hardware Exporter

Prometheus Hardware Exporter exports Prometheus metrics from BMCs (Baseboard
management controllers) using IPMI (Intelligent Platform Management Interface)
and Redfish protocol. It also exports and various SAS (Serial Attached SCSI) and
RAID (redundant array of inexpensive disks) controllers.

Prometheus Hardware Exporter is recommended for [Juju](https://juju.is/) users.
You can deploy Prometheus Hardware Exporter using the Hardware Observer charm.
For more information, you can read the documentation about Hardware Observer on
[Charmhub](https://charmhub.io/hardware-observer).

**Note**: this exporter does not bundle the required third party or proprietary
software. If you would like to use this exporter, you will need to install them
by yourself.

## Installation

This package is not published anywhere as of now. Currently, it can be installed
locally or on a virtual environment. To install it on a virtual environment,
run:

```shell
# Install virtualvenv and source it
pip3 install virtualenv
python3 -m venv venv
source venv/bin/activate

# Install the prometheus-hardware-exporter package; the "(venv)" prefix on the
# shell prompt indicates that the virtual environment is active.
(venv) pip3 install .
```

To verify that the package has been installed successfully, run:

```shell
(venv) prometheus-hardware-exporter -h
```

If you see the help message, then `prometheus-hardware-exporter` is installed on
the virtual environment.

## Usages

To start the exporter at port `10000` and enable the ipmi sensor collector, run:

```shell
(venv) prometheus-hardware-exporter -p 10000 --collector.ipmi_sensor
```

Metrics bind to `127.0.0.1` by default. Use `--bind-address <IPv4-address>`
(`bind_address` in YAML) to change this explicitly. Binding `0.0.0.0` exposes
metrics on every IPv4 interface; this endpoint has no authentication or TLS.
Use a protected network or authenticated proxy if remote access is required.
When `--config` is supplied, YAML configuration is used instead of CLI settings.

Note that all the exporters are disabled by default as you will need to install
the appropriate third party or proprietary software to run the collectors.  You
can check out [Resources](https://charmhub.io/hardware-observer/resources/) to
find out more information about the third party software.

## Supported Metrics

You can learn more about the metrics from [Hardware Observer
documentation](https://charmhub.io/hardware-observer/docs/metrics-and-alerts-common).

### Adaptec RAID

Install `arcconf` separately at `/usr/sbin/arcconf` (default), or set an explicit
absolute path with `--arcconf-path` / YAML `arcconf_path`. No `PATH` search or
shell is used. The binary and all parent directories must be trusted,
administrator-owned and not writable by the exporter account or untrusted users;
ownership and permissions are an installation responsibility, not checked by
the exporter. Missing/non-executable binaries report collection failure.
Enable with `--collector.adaptec_raid`, or add `collector.adaptec_raid` to
`enable_collectors` in YAML config. Disabled by default. Collector runs read-only
`arcconf LIST` and `arcconf GETCONFIG <id> AD`, `LD`, `PD` for each discovered
controller; `--collect-timeout` bounds each command (default 30 seconds).
`--collection-timeout` / YAML `collection_timeout` separately bounds the entire
Adaptec scan, including discovery (default 100 seconds; must be greater than 0
and at most 110 seconds). Every command uses the smaller of its per-command
timeout and the remaining monotonic scan budget. No new commands start once the
deadline is reached. This leaves at least 10 seconds before Alloy's 120-second
scrape timeout for subprocess cleanup, metric rendering and response delivery.
It is not an HTTP-wide deadline for other enabled collectors; enable only the
Adaptec collector on this endpoint to use that scrape budget. OS scheduling,
process creation and uninterruptible kernel I/O can delay cleanup beyond the
nominal deadline; this is not a hard real-time guarantee.

`arcconf_command_success` reports complete discovery/scan success;
`arcconf_command_ctrl_success{controller_id}` reports each discovered controller.
`arcconf_collection_incomplete` is 1 for discovery/command/parse failure, deadline
expiry, unexpected scan failure or overlapping scrape rejected by the existing
nonblocking lock; otherwise 0. `arcconf_collection_deadline_exceeded` is 1 only
when the total scan deadline expires, not on an ordinary per-command timeout.
On failure, completed controllers retain their current-scrape AD/LD/PD snapshots.
Failed or deadline-skipped controllers have per-controller success 0 and no
hardware samples. A per-command failure still allows later controllers to be
scanned while budget remains. No previous-scrape hardware samples are reused.

Example YAML (`prometheus-hardware-exporter --config config.yaml`):

```yaml
port: 10000
bind_address: 127.0.0.1
arcconf_path: /usr/sbin/arcconf
collect_timeout: 30
collection_timeout: 100
enable_collectors:
  - collector.adaptec_raid
```

Hardware status gauges report health separately: unknown/degraded states yield 0,
not command failure. Missing optional sensors yield no sample. No serial numbers,
WWNs, logical-drive names or mount paths are exported.

The feature branch's `AdaptecRAIDCollector` registration and
`adaptec_ready_logical_drives` / `adaptec_unready_logical_drives` gauges are retained.
Collection now uses separate AD/LD/PD commands instead of `GETCONFIG AL`.
Drive info labels are restricted: logical drives expose controller ID, logical-drive
ID, RAID level and state; physical drives expose controller ID, channel ID, device
ID, model and state. Previous name/size/raw-location labels are no longer exported.
Physical device IDs now identify channel/device locations, not `Device #` ordinals.

## Snap support

This is still work in progress, and only support local testing. For more
information on building and running the snap locally, please refer to
[README-SNAP.md](README-SNAP.md)
