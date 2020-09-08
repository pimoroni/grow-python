# Grow Service

This script will install Grow as a service on your Raspberry Pi, allowing it to run from boot and recover from errors.

# Useful Commands

* View service status: `systemctl status grow-monitor`
* Stop service: `sudo systemctl stop grow-monitor`
* Start service: `sudo systemctl start grow-monitor`
* View full debug/error output: `journalctl --no-pager --unit grow-monitor`

# Configuring Grow

You can configure grow using the on-screen UI, or by editing the settings in `/etc/default/grow`
