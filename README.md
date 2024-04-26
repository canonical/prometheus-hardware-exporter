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

Note that all the exporters are disabled by default as you will need to install
the appropriate third party or proprietary software to run the collectors.  You
can check out [Resources](https://charmhub.io/hardware-observer/resources/) to
find out more information about the third party software.

## Supported Metrics

You can learn more about the metrics from [Hardware Observer
documentation](https://charmhub.io/hardware-observer/docs/metrics-and-alerts-common).

## Snap support

This is still work in progress, and only support local testing. For more
information on building and running the snap locally, please refer to
[README-SNAP.md](README-SNAP.md)
