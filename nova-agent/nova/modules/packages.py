"""Unified package manager — npm, pip, cargo, go in one interface."""

import subprocess
from pathlib import Path

from nova.utils.display import (
    console, section_header, nova_table, summary_panel, metric_cards,
    success, info, warning, error, task_progress, completion_animation,
)


def detect_package_manager(directory: str = ".") -> dict:
    """Detect which package managers are in use."""
    root = Path(directory).expanduser().resolve()
    managers = {}

    checks = [
        ("npm", "package.json", "node_modules"),
        ("pip", "requirements.txt", None),
        ("pip", "pyproject.toml", None),
        ("pip", "setup.py", None),
        ("poetry", "poetry.lock", None),
        ("cargo", "Cargo.toml", "target"),
        ("go", "go.mod", None),
        ("composer", "composer.json", "vendor"),
        ("bundler", "Gemfile", None),
        ("pnpm", "pnpm-lock.yaml", "node_modules"),
        ("yarn", "yarn.lock", "node_modules"),
        ("bun", "bun.lockb", "node_modules"),
    ]

    for pm, config_file, deps_dir in checks:
        config_path = root / config_file
        if config_path.exists():
            has_deps = (root / deps_dir).exists() if deps_dir else True
            managers[pm] = {
                "config": config_file,
                "installed": has_deps,
                "path": str(config_path),
            }

    return managers


def show_detected(directory: str = "."):
    """Show detected package managers."""
    section_header("Package Managers", icon="📦")
    managers = detect_package_manager(directory)

    if not managers:
        info("No package managers detected in this directory")
        return

    table = nova_table("Detected", [
        ("Manager", "#00d4ff", {}),
        ("Config", "white", {}),
        ("Dependencies", "#7b68ee", {}),
    ])

    for pm, details in managers.items():
        installed = "[green]installed[/]" if details["installed"] else "[yellow]not installed[/]"
        table.add_row(pm, details["config"], installed)

    console.print(table)


def list_packages(directory: str = ".") -> dict:
    """List installed packages for detected managers."""
    root = Path(directory).expanduser().resolve()
    packages = {}

    # npm/pnpm/yarn/bun
    pkg_json = root / "package.json"
    if pkg_json.exists():
        import json
        try:
            pkg = json.loads(pkg_json.read_text())
            deps = pkg.get("dependencies", {})
            dev_deps = pkg.get("devDependencies", {})
            packages["npm"] = {
                "dependencies": deps,
                "devDependencies": dev_deps,
                "total": len(deps) + len(dev_deps),
            }
        except json.JSONDecodeError:
            pass

    # pip (requirements.txt)
    req_txt = root / "requirements.txt"
    if req_txt.exists():
        lines = [l.strip() for l in req_txt.read_text().splitlines()
                 if l.strip() and not l.startswith("#") and not l.startswith("-")]
        packages["pip"] = {
            "dependencies": {l.split("==")[0].split(">=")[0]: l for l in lines},
            "total": len(lines),
        }

    # pip (pyproject.toml)
    pyproject = root / "pyproject.toml"
    if pyproject.exists() and "pip" not in packages:
        try:
            import tomllib
        except ImportError:
            try:
                import tomli as tomllib
            except ImportError:
                tomllib = None
        if tomllib:
            try:
                data = tomllib.loads(pyproject.read_text())
                deps = data.get("project", {}).get("dependencies", [])
                packages["pip"] = {"dependencies": {d: d for d in deps}, "total": len(deps)}
            except Exception:
                pass

    # cargo
    cargo_toml = root / "Cargo.toml"
    if cargo_toml.exists():
        import re
        content = cargo_toml.read_text()
        deps = re.findall(r'^(\w[\w-]*)\s*=', content, re.MULTILINE)
        packages["cargo"] = {"dependencies": {d: d for d in deps}, "total": len(deps)}

    # go
    go_mod = root / "go.mod"
    if go_mod.exists():
        lines = [l.strip() for l in go_mod.read_text().splitlines()
                 if l.strip() and not l.startswith("module") and not l.startswith("go ")
                 and not l.startswith("//") and l.strip() not in ("require (", "require(", ")")]
        packages["go"] = {"dependencies": {l.split()[0]: l for l in lines if l}, "total": len(lines)}

    return packages


def show_packages(directory: str = "."):
    """Display packages across all detected managers."""
    section_header("Installed Packages", icon="📦")

    packages = list_packages(directory)
    if not packages:
        info("No packages found")
        return

    for pm, data in packages.items():
        deps = data.get("dependencies", {})
        dev_deps = data.get("devDependencies", {})

        table = nova_table(f"{pm} ({data['total']} packages)", [
            ("Package", "white", {}),
            ("Version/Spec", "#7b68ee", {}),
            ("Type", "dim", {}),
        ])

        for name, spec in list(deps.items())[:25]:
            table.add_row(name, str(spec), "dep")

        for name, spec in list(dev_deps.items())[:15]:
            table.add_row(name, str(spec), "dev")

        console.print(table)
        console.print()


def check_outdated(directory: str = "."):
    """Check for outdated packages."""
    root = Path(directory).expanduser().resolve()

    section_header("Outdated Packages", icon="📦")

    # npm
    if (root / "package.json").exists():
        info("Checking npm packages...")
        try:
            result = subprocess.run(
                ["npm", "outdated", "--json"],
                cwd=str(root), capture_output=True, text=True, timeout=30,
            )
            if result.stdout:
                import json
                outdated = json.loads(result.stdout)
                if outdated:
                    table = nova_table("npm — Outdated", [
                        ("Package", "white", {}),
                        ("Current", "#ff5e5e", {}),
                        ("Wanted", "#ffbb33", {}),
                        ("Latest", "#00ff88", {}),
                    ])
                    for name, info_data in list(outdated.items())[:20]:
                        table.add_row(
                            name,
                            info_data.get("current", "?"),
                            info_data.get("wanted", "?"),
                            info_data.get("latest", "?"),
                        )
                    console.print(table)
                else:
                    success("All npm packages up to date!")
        except (FileNotFoundError, subprocess.TimeoutExpired, Exception) as e:
            warning(f"npm check failed: {e}")

    # pip
    if (root / "requirements.txt").exists() or (root / "pyproject.toml").exists():
        info("Checking pip packages...")
        try:
            result = subprocess.run(
                ["pip", "list", "--outdated", "--format=json"],
                capture_output=True, text=True, timeout=30,
            )
            if result.stdout:
                import json
                outdated = json.loads(result.stdout)
                if outdated:
                    table = nova_table("pip — Outdated", [
                        ("Package", "white", {}),
                        ("Current", "#ff5e5e", {}),
                        ("Latest", "#00ff88", {}),
                    ])
                    for pkg in outdated[:20]:
                        table.add_row(pkg["name"], pkg["version"], pkg["latest_version"])
                    console.print(table)
                else:
                    success("All pip packages up to date!")
        except (FileNotFoundError, subprocess.TimeoutExpired, Exception) as e:
            warning(f"pip check failed: {e}")

    completion_animation("Dependency check complete!")
