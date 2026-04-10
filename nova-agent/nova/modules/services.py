"""Service and process manager — start, stop, restart, monitor services."""

import subprocess
import signal
import os
from pathlib import Path

import psutil

from nova.utils.display import (
    console, section_header, nova_table, summary_panel,
    success, info, warning, error, completion_animation,
)


def find_dev_servers() -> list[dict]:
    """Find running development servers."""
    dev_patterns = [
        ("Node.js", ["node"], [3000, 3001, 5173, 4321, 8080]),
        ("Python", ["python", "python3", "uvicorn", "gunicorn", "flask"], [8000, 8080, 5000]),
        ("Go", ["go"], [8080, 9090]),
        ("Ruby", ["ruby", "rails", "puma"], [3000, 4567]),
        ("Rust", ["cargo"], [8080]),
        ("Docker", ["docker", "docker-compose"], []),
    ]

    servers = []
    for proc in psutil.process_iter(["pid", "name", "cmdline", "connections", "create_time"]):
        try:
            pi = proc.info
            cmdline = " ".join(pi.get("cmdline") or [])[:100]

            for category, patterns, common_ports in dev_patterns:
                name = (pi.get("name") or "").lower()
                if any(p in name for p in patterns) or any(p in cmdline.lower() for p in patterns):
                    # Find listening ports
                    ports = []
                    try:
                        conns = proc.net_connections()
                        ports = list(set(
                            c.laddr.port for c in conns
                            if c.status == "LISTEN" and c.laddr
                        ))
                    except (psutil.AccessDenied, psutil.NoSuchProcess):
                        pass

                    if ports or any(p in cmdline for p in ["serve", "dev", "start", "run", "watch"]):
                        servers.append({
                            "pid": pi["pid"],
                            "category": category,
                            "name": pi.get("name", "?"),
                            "command": cmdline[:60],
                            "ports": ports,
                        })
                    break
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    return servers


def show_dev_servers():
    """Display running development servers."""
    section_header("Development Servers", icon="🖥")

    servers = find_dev_servers()
    if not servers:
        info("No development servers detected")
        return

    table = nova_table(f"Running Servers ({len(servers)})", [
        ("PID", "dim", {"justify": "right", "width": 7}),
        ("Type", "#00d4ff", {}),
        ("Process", "white", {}),
        ("Ports", "#00ff88", {}),
        ("Command", "dim", {"max_width": 40}),
    ])

    for s in servers:
        ports = ", ".join(str(p) for p in s["ports"]) if s["ports"] else "—"
        table.add_row(str(s["pid"]), s["category"], s["name"], ports, s["command"])

    console.print(table)


def find_listening_ports() -> list[dict]:
    """Find all processes listening on ports."""
    listeners = {}
    for conn in psutil.net_connections(kind="inet"):
        if conn.status == "LISTEN" and conn.laddr:
            port = conn.laddr.port
            if port not in listeners:
                try:
                    proc = psutil.Process(conn.pid)
                    listeners[port] = {
                        "port": port,
                        "pid": conn.pid,
                        "name": proc.name(),
                        "address": f"{conn.laddr.ip}:{conn.laddr.port}",
                    }
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    listeners[port] = {
                        "port": port,
                        "pid": conn.pid,
                        "name": "?",
                        "address": f"{conn.laddr.ip}:{conn.laddr.port}",
                    }

    return sorted(listeners.values(), key=lambda x: x["port"])


def show_listeners():
    """Display all listening ports and their processes."""
    section_header("Listening Ports", icon="🔌")

    listeners = find_listening_ports()
    if not listeners:
        info("No listening ports found")
        return

    table = nova_table(f"Listening ({len(listeners)} ports)", [
        ("Port", "#00d4ff", {"justify": "right"}),
        ("PID", "dim", {"justify": "right"}),
        ("Process", "white", {}),
        ("Address", "dim", {}),
    ])

    for l in listeners:
        table.add_row(str(l["port"]), str(l["pid"]), l["name"], l["address"])

    console.print(table)


def kill_process(pid: int):
    """Kill a process by PID."""
    try:
        proc = psutil.Process(pid)
        name = proc.name()
        proc.terminate()
        proc.wait(timeout=5)
        success(f"Terminated process {pid} ({name})")
    except psutil.NoSuchProcess:
        error(f"Process {pid} not found")
    except psutil.TimeoutExpired:
        try:
            proc.kill()
            success(f"Force-killed process {pid}")
        except psutil.NoSuchProcess:
            pass
    except psutil.AccessDenied:
        error(f"Permission denied for PID {pid}")


def kill_port(port: int):
    """Kill whatever process is listening on a port."""
    for conn in psutil.net_connections(kind="inet"):
        if conn.status == "LISTEN" and conn.laddr and conn.laddr.port == port:
            kill_process(conn.pid)
            return

    error(f"No process found listening on port {port}")


def show_resource_hogs(limit: int = 10):
    """Show processes using the most resources."""
    section_header("Resource Hogs", icon="🐷")

    procs = []
    for proc in psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent", "memory_info"]):
        try:
            pi = proc.info
            procs.append(pi)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    # Top CPU
    by_cpu = sorted(procs, key=lambda p: p.get("cpu_percent", 0), reverse=True)[:limit]
    table = nova_table("Top CPU Consumers", [
        ("PID", "dim", {"justify": "right", "width": 7}),
        ("Process", "white", {"min_width": 20}),
        ("CPU %", "#ff5e5e", {"justify": "right"}),
        ("Memory", "#7b68ee", {"justify": "right"}),
    ])
    for p in by_cpu:
        table.add_row(
            str(p.get("pid", "")),
            (p.get("name") or "?")[:25],
            f"{p.get('cpu_percent', 0):.1f}%",
            _h(p.get("memory_info", None).rss if p.get("memory_info") else 0),
        )
    console.print(table)

    console.print()

    # Top Memory
    by_mem = sorted(procs, key=lambda p: (p.get("memory_info") or type("", (), {"rss": 0})).rss, reverse=True)[:limit]
    table = nova_table("Top Memory Consumers", [
        ("PID", "dim", {"justify": "right", "width": 7}),
        ("Process", "white", {"min_width": 20}),
        ("Memory", "#ff6ec7", {"justify": "right"}),
        ("CPU %", "dim", {"justify": "right"}),
    ])
    for p in by_mem:
        table.add_row(
            str(p.get("pid", "")),
            (p.get("name") or "?")[:25],
            _h(p.get("memory_info", type("", (), {"rss": 0})).rss),
            f"{p.get('cpu_percent', 0):.1f}%",
        )
    console.print(table)


def _h(b) -> str:
    if not b:
        return "0B"
    for unit in ["B", "KB", "MB", "GB"]:
        if b < 1024:
            return f"{b:.1f}{unit}"
        b /= 1024
    return f"{b:.1f}TB"
