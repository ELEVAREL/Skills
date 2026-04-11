"""Nova service installer — run Nova as a 24/7 background process.

Picks the right installer for the host OS:
  - Linux: systemd user unit
  - macOS: launchd plist in ~/Library/LaunchAgents
  - Windows: Task Scheduler (no admin required)

All three modes launch `python -m nova.cli gateway start --background` and
keep it alive across reboots without requiring root/admin.
"""

from nova.service.manager import (
    get_platform_installer,
    install_service,
    uninstall_service,
    service_status,
    start_service,
    stop_service,
)

__all__ = [
    "get_platform_installer",
    "install_service",
    "uninstall_service",
    "service_status",
    "start_service",
    "stop_service",
]
