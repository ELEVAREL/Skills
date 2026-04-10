"""Network diagnostics module — connectivity, speed, ports, and DNS."""

import socket
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from nova.utils.display import (
    console, success, info, warning, error, section_header,
    stats_table, summary_panel, task_progress,
)


def check_connectivity() -> dict:
    """Check internet connectivity and DNS resolution."""
    results = {}

    targets = [
        ("DNS Resolution", "google.com", 443),
        ("Google", "google.com", 443),
        ("Cloudflare DNS", "1.1.1.1", 443),
        ("GitHub", "github.com", 443),
        ("AWS", "aws.amazon.com", 443),
    ]

    for name, host, port in targets:
        start = time.time()
        try:
            if name == "DNS Resolution":
                socket.getaddrinfo(host, port)
            else:
                sock = socket.create_connection((host, port), timeout=5)
                sock.close()
            latency = (time.time() - start) * 1000
            results[name] = f"[green]OK[/] ({latency:.0f}ms)"
        except (socket.timeout, socket.error, OSError):
            results[name] = "[red]FAILED[/]"

    return results


def show_connectivity():
    """Display connectivity check results."""
    section_header("Network Connectivity")
    with task_progress("Checking connectivity") as progress:
        task = progress.add_task("Testing connections", total=5)
        results = {}
        targets = [
            ("DNS Resolution", "google.com", 443),
            ("Google", "google.com", 443),
            ("Cloudflare DNS", "1.1.1.1", 443),
            ("GitHub", "github.com", 443),
            ("AWS", "aws.amazon.com", 443),
        ]
        for name, host, port in targets:
            start = time.time()
            try:
                sock = socket.create_connection((host, port), timeout=5)
                sock.close()
                latency = (time.time() - start) * 1000
                results[name] = f"[green]OK[/] ({latency:.0f}ms)"
            except (socket.timeout, socket.error, OSError):
                results[name] = "[red]FAILED[/]"
            progress.update(task, advance=1)

    console.print(stats_table(results, title="Connectivity"))


def get_network_info() -> dict:
    """Get network interface information."""
    import psutil
    info_dict = {}

    addrs = psutil.net_if_addrs()
    stats = psutil.net_if_stats()

    for iface, addr_list in addrs.items():
        if iface == "lo":
            continue
        iface_info = {"status": "up" if stats.get(iface, None) and stats[iface].isup else "down"}
        for addr in addr_list:
            if addr.family == socket.AF_INET:
                iface_info["ipv4"] = addr.address
            elif addr.family == socket.AF_INET6:
                iface_info["ipv6"] = addr.address[:30]
        if "ipv4" in iface_info:
            info_dict[iface] = iface_info

    return info_dict


def show_network_info():
    """Display network interface information."""
    from rich.table import Table

    net_info = get_network_info()
    table = Table(title="Network Interfaces", border_style="dim cyan", header_style="bold cyan")
    table.add_column("Interface", style="white")
    table.add_column("IPv4", style="cyan")
    table.add_column("Status", style="green")

    for iface, details in net_info.items():
        status = "[green]UP[/]" if details["status"] == "up" else "[red]DOWN[/]"
        table.add_row(iface, details.get("ipv4", "—"), status)

    console.print(table)


def get_public_ip() -> str | None:
    """Get public IP address."""
    import urllib.request
    try:
        return urllib.request.urlopen("https://api.ipify.org", timeout=5).read().decode()
    except Exception:
        return None


def scan_ports(host: str = "localhost", ports: list[int] | None = None) -> list[dict]:
    """Scan common ports on a host."""
    if ports is None:
        ports = [22, 80, 443, 3000, 3306, 5432, 5433, 6379, 8000, 8080, 8443, 9090, 27017]

    common_services = {
        22: "SSH", 80: "HTTP", 443: "HTTPS", 3000: "Dev Server",
        3306: "MySQL", 5432: "PostgreSQL", 5433: "PostgreSQL",
        6379: "Redis", 8000: "Dev Server", 8080: "HTTP Alt",
        8443: "HTTPS Alt", 9090: "Prometheus", 27017: "MongoDB",
    }

    results = []

    def check_port(port):
        try:
            sock = socket.create_connection((host, port), timeout=1)
            sock.close()
            return {"port": port, "status": "open", "service": common_services.get(port, "unknown")}
        except (socket.timeout, socket.error, OSError):
            return {"port": port, "status": "closed", "service": common_services.get(port, "")}

    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = {executor.submit(check_port, p): p for p in ports}
        for future in as_completed(futures):
            results.append(future.result())

    return sorted(results, key=lambda r: r["port"])


def show_ports(host: str = "localhost"):
    """Display open ports scan."""
    from rich.table import Table

    section_header(f"Port Scan: {host}")
    with task_progress("Scanning ports") as progress:
        task = progress.add_task("Scanning", total=1)
        results = scan_ports(host)
        progress.update(task, advance=1)

    table = Table(border_style="dim cyan", header_style="bold cyan")
    table.add_column("Port", style="cyan", justify="right")
    table.add_column("Status")
    table.add_column("Service", style="dim")

    for r in results:
        status = "[green]OPEN[/]" if r["status"] == "open" else "[dim]closed[/]"
        if r["status"] == "open":
            table.add_row(str(r["port"]), status, r["service"])

    open_count = sum(1 for r in results if r["status"] == "open")
    console.print(table)
    info(f"{open_count} open ports found")


def get_bandwidth() -> dict:
    """Get current network bandwidth usage."""
    import psutil
    counters1 = psutil.net_io_counters()
    time.sleep(1)
    counters2 = psutil.net_io_counters()

    sent_per_sec = counters2.bytes_sent - counters1.bytes_sent
    recv_per_sec = counters2.bytes_recv - counters1.bytes_recv

    return {
        "upload_speed": _humanize_speed(sent_per_sec),
        "download_speed": _humanize_speed(recv_per_sec),
        "total_sent": _humanize_bytes(counters2.bytes_sent),
        "total_received": _humanize_bytes(counters2.bytes_recv),
        "packets_sent": counters2.packets_sent,
        "packets_received": counters2.packets_recv,
    }


def _humanize_speed(bytes_per_sec: float) -> str:
    for unit in ["B/s", "KB/s", "MB/s", "GB/s"]:
        if bytes_per_sec < 1024:
            return f"{bytes_per_sec:.1f} {unit}"
        bytes_per_sec /= 1024
    return f"{bytes_per_sec:.1f} TB/s"


def _humanize_bytes(b: int) -> str:
    for unit in ["B", "KB", "MB", "GB"]:
        if b < 1024:
            return f"{b:.1f} {unit}"
        b /= 1024
    return f"{b:.1f} TB"
