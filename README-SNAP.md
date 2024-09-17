# Prometheus Hardware Exporter Snap

**Work In Progress**: the snap is only ready for local testing.

## Local Build and Testing

You need `snapcraft` to build the snap:

```shell
sudo snap install snapcraft --classic
```

Snapcraft also requires backend to create isolated build environment. You can
choose either of the following two backends for snapcraft:

- [LXD](https://linuxcontainers.org/lxd/introduction/), which creates container
  image build instances. It can be used inside virtual machines.
- [Multipass](https://multipass.run/), which creates virtual machine build
  instances. It cannot be reliably used on platforms that do not support nested
  virtualization. For instance, Multipass will most likely not run inside a
  virtual machine itself.

To build the snap:

```shell
snapcraft --use-lxd
```

To try the snap that was built, you can install it locally:

```shell
sudo snap install --devmode ./$(grep -E "^name:" snap/snapcraft.yaml | awk '{print $2}').snap
```

Start the exporter:

```shell
sudo snap start prometheus-hardware-exporter  # by default it listen on port 10000
```

When you're done testing, you can remove the snap:

```shell
sudo snap remove prometheus-hardware-exporter
```

## Snap Configuration

The install hook (`./snap/hooks/install`) will generate a default configuration
for the exporter. By default, the exporter is started at port 10000 with a
logging level of INFO.

You can change the default configuration by editing

```shell
/var/snap/prometheus-hardware-exporter/current/config.yaml
```

and then restart the snap by

```shell
sudo snap restart prometheus-hardware-exporter
```
