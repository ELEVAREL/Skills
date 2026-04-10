"""Code analyzer — leverages skills for security review, tech debt, and code quality."""

import os
import re
import subprocess
from pathlib import Path
from collections import defaultdict, Counter

from nova.utils.display import (
    console, section_header, summary_panel, nova_table, metric_cards,
    success, info, warning, error, task_progress, completion_animation,
)


def analyze_codebase(directory: str = ".") -> dict:
    """Full codebase analysis — language stats, complexity, issues."""
    root = Path(directory).expanduser().resolve()

    results = {
        "languages": Counter(),
        "line_counts": Counter(),
        "file_counts": Counter(),
        "issues": [],
        "todos": [],
        "large_functions": [],
        "security_flags": [],
        "test_coverage": {"test_files": 0, "source_files": 0},
    }

    skip = {".git", "node_modules", "__pycache__", ".venv", "venv", "dist", "build",
            ".next", ".nuxt", "coverage", ".tox", "target", "vendor"}

    ext_to_lang = {
        ".py": "Python", ".js": "JavaScript", ".ts": "TypeScript",
        ".jsx": "React JSX", ".tsx": "React TSX", ".go": "Go",
        ".rs": "Rust", ".java": "Java", ".rb": "Ruby", ".php": "PHP",
        ".c": "C", ".cpp": "C++", ".h": "C/C++ Header",
        ".cs": "C#", ".swift": "Swift", ".kt": "Kotlin",
        ".sh": "Shell", ".bash": "Shell", ".sql": "SQL",
        ".html": "HTML", ".css": "CSS", ".scss": "SCSS",
        ".yaml": "YAML", ".yml": "YAML", ".json": "JSON",
        ".md": "Markdown", ".toml": "TOML", ".xml": "XML",
    }

    security_patterns = [
        (r"(?i)(password|passwd|secret|token|api_key)\s*=\s*['\"][^'\"]+['\"]", "Hardcoded secret"),
        (r"(?i)eval\s*\(", "eval() usage — potential code injection"),
        (r"(?i)exec\s*\(", "exec() usage — potential code injection"),
        (r"(?i)innerHTML\s*=", "innerHTML assignment — potential XSS"),
        (r"(?i)dangerouslySetInnerHTML", "dangerouslySetInnerHTML — potential XSS"),
        (r"(?i)subprocess\.call\(.*shell\s*=\s*True", "Shell injection risk"),
        (r"(?i)SELECT.*FROM.*WHERE.*\+|f['\"]SELECT", "Possible SQL injection"),
    ]

    with task_progress("Analyzing codebase") as progress:
        # Count files first
        all_files = []
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if d not in skip and not d.startswith(".")]
            for name in filenames:
                ext = Path(name).suffix.lower()
                if ext in ext_to_lang:
                    all_files.append((Path(dirpath) / name, ext))

        task = progress.add_task("Scanning files", total=len(all_files))

        for filepath, ext in all_files:
            lang = ext_to_lang[ext]
            results["languages"][lang] += 1
            results["file_counts"][lang] += 1

            # Test file detection
            name_lower = filepath.name.lower()
            if any(p in name_lower for p in ["test_", "_test.", ".test.", ".spec.", "test.", "spec."]):
                results["test_coverage"]["test_files"] += 1
            else:
                results["test_coverage"]["source_files"] += 1

            try:
                content = filepath.read_text(errors="ignore")
                lines = content.splitlines()
                results["line_counts"][lang] += len(lines)

                # Find TODOs and FIXMEs
                for i, line in enumerate(lines, 1):
                    stripped = line.strip()
                    if re.search(r"(?i)\b(TODO|FIXME|HACK|XXX|BUG)\b", stripped):
                        marker = re.search(r"(?i)\b(TODO|FIXME|HACK|XXX|BUG)\b", stripped).group()
                        results["todos"].append({
                            "file": str(filepath.relative_to(root)),
                            "line": i,
                            "type": marker.upper(),
                            "text": stripped[:100],
                        })

                    # Security scan
                    for pattern, desc in security_patterns:
                        if re.search(pattern, stripped):
                            results["security_flags"].append({
                                "file": str(filepath.relative_to(root)),
                                "line": i,
                                "issue": desc,
                                "code": stripped[:80],
                            })

                # Large function detection (Python/JS/TS)
                if ext in (".py", ".js", ".ts", ".jsx", ".tsx"):
                    func_pattern = r"(?:def |function |const \w+ = (?:async )?\(|(?:async )?(?:\w+)\s*\()"
                    func_start = None
                    func_name = ""
                    for i, line in enumerate(lines, 1):
                        if re.match(r"\s*(?:def |function |(?:export )?(?:const|let) \w+ = )", line):
                            if func_start and (i - func_start) > 50:
                                results["large_functions"].append({
                                    "file": str(filepath.relative_to(root)),
                                    "function": func_name,
                                    "lines": i - func_start,
                                    "start": func_start,
                                })
                            func_start = i
                            func_name = line.strip()[:60]
                    # Check last function
                    if func_start and (len(lines) - func_start) > 50:
                        results["large_functions"].append({
                            "file": str(filepath.relative_to(root)),
                            "function": func_name,
                            "lines": len(lines) - func_start,
                            "start": func_start,
                        })

            except (PermissionError, OSError, UnicodeDecodeError):
                pass

            progress.update(task, advance=1)

    return results


def show_codebase_analysis(directory: str = "."):
    """Display a comprehensive codebase analysis."""
    section_header("Codebase Analysis", icon="🔍")

    results = analyze_codebase(directory)

    total_files = sum(results["file_counts"].values())
    total_lines = sum(results["line_counts"].values())
    total_langs = len(results["languages"])

    # Metric cards
    metric_cards([
        {"label": "Files", "value": f"{total_files:,}", "color": "#00d4ff", "icon": "📁"},
        {"label": "Lines", "value": f"{total_lines:,}", "color": "#7b68ee", "icon": "📝"},
        {"label": "Languages", "value": str(total_langs), "color": "#00ff88", "icon": "🌐"},
        {"label": "Issues", "value": str(len(results["security_flags"])), "color": "#ff5e5e", "icon": "🛡"},
    ])

    # Language breakdown
    console.print()
    table = nova_table("Languages", [
        ("Language", "#00d4ff", {}),
        ("Files", "white", {"justify": "right"}),
        ("Lines", "white", {"justify": "right"}),
        ("Share", "#7b68ee", {"justify": "right"}),
    ])
    for lang, count in results["line_counts"].most_common(15):
        share = (count / total_lines * 100) if total_lines > 0 else 0
        table.add_row(lang, str(results["file_counts"][lang]), f"{count:,}", f"{share:.1f}%")
    console.print(table)

    # Test coverage estimate
    tc = results["test_coverage"]
    test_ratio = (tc["test_files"] / max(1, tc["source_files"])) * 100
    test_color = "#00ff88" if test_ratio > 50 else "#ffbb33" if test_ratio > 20 else "#ff5e5e"
    console.print()
    summary_panel("Test Coverage Estimate", {
        "Test files": str(tc["test_files"]),
        "Source files": str(tc["source_files"]),
        "Test ratio": f"[{test_color}]{test_ratio:.0f}%[/]",
    }, style="#7b68ee")

    # TODOs
    if results["todos"]:
        console.print()
        todo_counts = Counter(t["type"] for t in results["todos"])
        table = nova_table(f"Technical Debt Markers ({len(results['todos'])} found)", [
            ("Type", "#ffbb33", {}),
            ("File", "dim", {}),
            ("Line", "dim", {"justify": "right"}),
            ("Content", "white", {"max_width": 60}),
        ])
        for t in results["todos"][:20]:
            table.add_row(t["type"], t["file"], str(t["line"]), t["text"])
        console.print(table)

    # Security flags
    if results["security_flags"]:
        console.print()
        table = nova_table(f"Security Flags ({len(results['security_flags'])} found)", [
            ("Issue", "#ff5e5e", {}),
            ("File", "dim", {}),
            ("Line", "dim", {"justify": "right"}),
            ("Code", "dim", {"max_width": 50}),
        ])
        for s in results["security_flags"][:15]:
            table.add_row(s["issue"], s["file"], str(s["line"]), s["code"])
        console.print(table)

    # Large functions
    if results["large_functions"]:
        console.print()
        results["large_functions"].sort(key=lambda f: f["lines"], reverse=True)
        table = nova_table(f"Large Functions (>{50} lines)", [
            ("Function", "white", {"max_width": 40}),
            ("File", "dim", {}),
            ("Lines", "#ffbb33", {"justify": "right"}),
        ])
        for f in results["large_functions"][:10]:
            table.add_row(f["function"], f["file"], str(f["lines"]))
        console.print(table)

    completion_animation("Analysis complete!")
    return results
