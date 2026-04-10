"""Project scaffolder — create new projects with best-practice structure."""

import os
from pathlib import Path

from nova.utils.display import (
    console, section_header, success, info, warning, error,
    completion_animation, multi_step_progress,
)


TEMPLATES = {
    "python": {
        "name": "Python Package",
        "files": {
            "src/{name}/__init__.py": '"""{{name}} — created by Nova."""\n\n__version__ = "0.1.0"\n',
            "src/{name}/main.py": 'def main():\n    """Entry point."""\n    print("Hello from {name}!")\n\n\nif __name__ == "__main__":\n    main()\n',
            "tests/__init__.py": "",
            "tests/test_main.py": 'from {name}.main import main\n\n\ndef test_main(capsys):\n    main()\n    captured = capsys.readouterr()\n    assert "{name}" in captured.out\n',
            "pyproject.toml": '[build-system]\nrequires = ["setuptools>=68.0"]\nbuild-backend = "setuptools.backends._legacy:_Backend"\n\n[project]\nname = "{name}"\nversion = "0.1.0"\nrequires-python = ">=3.10"\n\n[project.scripts]\n{name} = "{name}.main:main"\n\n[tool.ruff]\nline-length = 100\n\n[tool.pytest.ini_options]\ntestpaths = ["tests"]\n',
            ".gitignore": "__pycache__/\n*.pyc\n.venv/\ndist/\n*.egg-info/\n.ruff_cache/\n.pytest_cache/\n.coverage\n",
            "README.md": "# {name}\n\nCreated with Nova Agent.\n\n## Setup\n\n```bash\npip install -e .\n```\n\n## Test\n\n```bash\npytest\n```\n",
            ".claude/CLAUDE.md": "# {name}\n\nPython project. Use pytest for tests, ruff for linting.\n",
        },
    },
    "node": {
        "name": "Node.js / TypeScript",
        "files": {
            "src/index.ts": 'export function main(): void {{\n  console.log("Hello from {name}!");\n}}\n\nmain();\n',
            "src/utils.ts": 'export function greet(name: string): string {{\n  return `Hello, ${{name}}!`;\n}}\n',
            "tests/index.test.ts": 'import {{ describe, it, expect }} from "vitest";\nimport {{ greet }} from "../src/utils";\n\ndescribe("greet", () => {{\n  it("returns greeting", () => {{\n    expect(greet("World")).toBe("Hello, World!");\n  }});\n}});\n',
            "package.json": '{{\n  "name": "{name}",\n  "version": "0.1.0",\n  "type": "module",\n  "scripts": {{\n    "build": "tsc",\n    "dev": "tsx src/index.ts",\n    "test": "vitest run",\n    "lint": "eslint src/"\n  }},\n  "devDependencies": {{\n    "typescript": "^5.4.0",\n    "tsx": "^4.0.0",\n    "vitest": "^2.0.0",\n    "eslint": "^9.0.0"\n  }}\n}}\n',
            "tsconfig.json": '{{\n  "compilerOptions": {{\n    "target": "ES2022",\n    "module": "ESNext",\n    "moduleResolution": "bundler",\n    "strict": true,\n    "outDir": "dist",\n    "rootDir": "src"\n  }},\n  "include": ["src"]\n}}\n',
            ".gitignore": "node_modules/\ndist/\n.env\ncoverage/\n",
            "README.md": "# {name}\n\nCreated with Nova Agent.\n\n## Setup\n\n```bash\nnpm install\n```\n\n## Dev\n\n```bash\nnpm run dev\n```\n\n## Test\n\n```bash\nnpm test\n```\n",
            ".claude/CLAUDE.md": "# {name}\n\nTypeScript project. Use vitest for tests, eslint for linting.\n",
        },
    },
    "react": {
        "name": "React + Vite + TypeScript",
        "files": {
            "src/App.tsx": 'export default function App() {{\n  return (\n    <main>\n      <h1>{name}</h1>\n      <p>Built with Nova Agent</p>\n    </main>\n  );\n}}\n',
            "src/main.tsx": 'import React from "react";\nimport ReactDOM from "react-dom/client";\nimport App from "./App";\n\nReactDOM.createRoot(document.getElementById("root")!).render(\n  <React.StrictMode>\n    <App />\n  </React.StrictMode>\n);\n',
            "src/index.css": ':root {{\n  font-family: system-ui, sans-serif;\n  line-height: 1.5;\n  color: #213547;\n  background: #ffffff;\n}}\n\nbody {{ margin: 0; padding: 2rem; }}\n',
            "index.html": '<!DOCTYPE html>\n<html lang="en">\n<head>\n  <meta charset="UTF-8" />\n  <meta name="viewport" content="width=device-width, initial-scale=1.0" />\n  <title>{name}</title>\n</head>\n<body>\n  <div id="root"></div>\n  <script type="module" src="/src/main.tsx"></script>\n</body>\n</html>\n',
            "package.json": '{{\n  "name": "{name}",\n  "version": "0.1.0",\n  "type": "module",\n  "scripts": {{\n    "dev": "vite",\n    "build": "tsc && vite build",\n    "preview": "vite preview",\n    "test": "vitest run"\n  }},\n  "devDependencies": {{\n    "typescript": "^5.4.0",\n    "vite": "^6.0.0",\n    "@vitejs/plugin-react": "^4.0.0",\n    "vitest": "^2.0.0"\n  }},\n  "dependencies": {{\n    "react": "^19.0.0",\n    "react-dom": "^19.0.0"\n  }}\n}}\n',
            "tsconfig.json": '{{\n  "compilerOptions": {{\n    "target": "ES2022",\n    "module": "ESNext",\n    "moduleResolution": "bundler",\n    "jsx": "react-jsx",\n    "strict": true\n  }},\n  "include": ["src"]\n}}\n',
            ".gitignore": "node_modules/\ndist/\n.env\n",
            "README.md": "# {name}\n\nReact + Vite + TypeScript. Created with Nova Agent.\n\n```bash\nnpm install && npm run dev\n```\n",
        },
    },
    "api": {
        "name": "REST API (Express + TypeScript)",
        "files": {
            "src/index.ts": 'import express from "express";\n\nconst app = express();\nconst port = process.env.PORT || 3000;\n\napp.use(express.json());\n\napp.get("/health", (_req, res) => {{\n  res.json({{ status: "ok", timestamp: new Date().toISOString() }});\n}});\n\napp.get("/api/hello", (_req, res) => {{\n  res.json({{ message: "Hello from {name}!" }});\n}});\n\napp.listen(port, () => {{\n  console.log(`Server running on port ${{port}}`);\n}});\n',
            "src/middleware/errorHandler.ts": 'import {{ Request, Response, NextFunction }} from "express";\n\nexport function errorHandler(err: Error, _req: Request, res: Response, _next: NextFunction) {{\n  console.error(err.stack);\n  res.status(500).json({{ error: "Internal server error" }});\n}}\n',
            "tests/api.test.ts": 'import {{ describe, it, expect }} from "vitest";\n\ndescribe("API", () => {{\n  it("should be testable", () => {{\n    expect(true).toBe(true);\n  }});\n}});\n',
            "Dockerfile": 'FROM node:20-alpine AS builder\nWORKDIR /app\nCOPY package*.json ./\nRUN npm ci\nCOPY . .\nRUN npm run build\n\nFROM node:20-alpine\nWORKDIR /app\nCOPY --from=builder /app/dist ./dist\nCOPY --from=builder /app/node_modules ./node_modules\nUSER node\nEXPOSE 3000\nCMD ["node", "dist/index.js"]\n',
            "package.json": '{{\n  "name": "{name}",\n  "version": "0.1.0",\n  "type": "module",\n  "scripts": {{\n    "dev": "tsx watch src/index.ts",\n    "build": "tsc",\n    "start": "node dist/index.js",\n    "test": "vitest run"\n  }},\n  "dependencies": {{\n    "express": "^5.0.0"\n  }},\n  "devDependencies": {{\n    "typescript": "^5.4.0",\n    "tsx": "^4.0.0",\n    "@types/express": "^5.0.0",\n    "vitest": "^2.0.0"\n  }}\n}}\n',
            ".gitignore": "node_modules/\ndist/\n.env\n",
            ".env.example": "PORT=3000\nNODE_ENV=development\n",
            "README.md": "# {name}\n\nREST API. Created with Nova Agent.\n\n```bash\nnpm install && npm run dev\n```\n\nHealth check: http://localhost:3000/health\n",
        },
    },
}


def list_templates():
    """Show available project templates."""
    from rich.table import Table
    from rich import box as b

    section_header("Project Templates", icon="🏗")

    table = Table(border_style="dim #5b50ff", header_style="bold #00d4ff",
                  box=b.SIMPLE_HEAD, padding=(0, 2))
    table.add_column("Template", style="#00d4ff")
    table.add_column("Description", style="white")
    table.add_column("Includes", style="dim")

    details = {
        "python": "Tests, linting, pyproject.toml, CLAUDE.md",
        "node": "TypeScript, Vitest, ESLint, CLAUDE.md",
        "react": "Vite, TypeScript, React 19, CSS",
        "api": "Express, TypeScript, Docker, health check",
    }

    for key, tmpl in TEMPLATES.items():
        table.add_row(key, tmpl["name"], details.get(key, ""))

    console.print(table)


def scaffold_project(template: str, name: str, directory: str = "."):
    """Create a new project from a template."""
    if template not in TEMPLATES:
        error(f"Unknown template: {template}")
        info(f"Available: {', '.join(TEMPLATES.keys())}")
        return

    tmpl = TEMPLATES[template]
    project_dir = Path(directory).expanduser().resolve() / name

    if project_dir.exists():
        error(f"Directory already exists: {project_dir}")
        return

    section_header(f"Creating: {tmpl['name']} — {name}", icon="🏗")

    files = tmpl["files"]
    created = 0

    for rel_path, content in files.items():
        actual_path = rel_path.replace("{name}", name)
        filepath = project_dir / actual_path
        filepath.parent.mkdir(parents=True, exist_ok=True)

        actual_content = content.replace("{name}", name)
        filepath.write_text(actual_content)
        created += 1
        info(f"Created {actual_path}")

    # Initialize git
    import subprocess
    subprocess.run(["git", "init", "--quiet"], cwd=str(project_dir),
                   capture_output=True, timeout=10)
    subprocess.run(["git", "add", "."], cwd=str(project_dir),
                   capture_output=True, timeout=10)
    subprocess.run(["git", "commit", "-m", "Initial commit (scaffolded by Nova)","--quiet"],
                   cwd=str(project_dir), capture_output=True, timeout=10)

    console.print()
    completion_animation(f"Project '{name}' created with {created} files!")
    console.print()
    info(f"Location: {project_dir}")
    info(f"Next: cd {name} && {'pip install -e .' if template == 'python' else 'npm install'}")
