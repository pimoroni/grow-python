# Grow Service

This script will install Grow as a service on your Raspberry Pi, allowing it to run at boot and recover from errors.

# Installing

```
sudo ./install.sh
```

# Useful Commands

* View service status: `systemctl status grow-monitor`
* Stop service: `sudo systemctl stop grow-monitor`
* Start service: `sudo systemctl start grow-monitor`
* View full debug/error output: `journalctl --no-pager --unit grow-monitor`

# Configuring Grow

You can configure grow using the on-screen UI, or by editing the settings in `/etc/default/grow`.

[See the examples README.md](../examples/README.md#channel-settings) for an explanation of the options.
