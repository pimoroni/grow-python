#!/bin/bash

user_check() {
	if [ $(id -u) -ne 0 ]; then
		printf "Script must be run as root. Try 'sudo ./install.sh'\n"
		exit 1
	fi
}

success() {
	echo -e "$(tput setaf 2)$1$(tput sgr0)"
}

inform() {
	echo -e "$(tput setaf 6)$1$(tput sgr0)"
}

warning() {
	echo -e "$(tput setaf 1)$1$(tput sgr0)"
}

user_check

inform "Copying icons to /usr/share/grow-monitor...\n"
mkdir -p /usr/share/grow-monitor/icons
cp ../examples/icons/* /usr/share/grow-monitor/icons

inform "Installing grow-monitor to /usr/bin/grow-monitor...\n"
cp ../examples/monitor.py /usr/bin/grow-monitor
chmod +x /usr/bin/grow-monitor

inform "Installing settings to /etc/default/grow...\n"
cp ../examples/settings.yml /etc/default/grow

inform "Installing systemd service...\n"
cp grow-monitor.service /etc/systemd/system/
systemctl reenable grow-monitor.service
systemctl start grow-monitor.service

inform "\nTo see grow debug output, run: \"journalctl --no-pager --unit grow-monitor\"\n"
