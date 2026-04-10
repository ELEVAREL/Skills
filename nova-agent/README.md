# Nova Agent

AI-powered CLI agent for organizing your computer and automating tasks. Works like Claude Code but for your file system and daily computer management.

## Features

- **File Organizer** — Automatically categorize and sort files (Documents, Images, Code, etc.)
- **Directory Analyzer** — Scan directories for statistics, duplicates, and large files
- **File Watcher** — Auto-organize new files as they arrive (e.g., Downloads folder)
- **System Monitor** — CPU, memory, disk usage, top processes
- **Cleanup Finder** — Find caches, temp files, and large files to reclaim space
- **AI Chat** — Natural language interface powered by Claude for any computer task
- **Interactive Shell** — Rich terminal UI with command history and autocomplete

## Install

```bash
cd nova-agent
pip install -e .
```

Set your API key for AI features:
```bash
export ANTHROPIC_API_KEY=your-key-here
```

## Usage

### Interactive Mode (like Claude Code)

```bash
nova
```

This opens an interactive shell where you can:
- Type natural language: `"organize my Downloads folder"`
- Use slash commands: `/organize ~/Downloads`
- Ask questions: `"what's using the most disk space?"`

### Direct Commands

```bash
# Organize files (dry-run by default)
nova organize ~/Downloads
nova organize ~/Downloads --execute          # Actually move files
nova organize ~/Downloads --dest ~/Sorted    # Custom destination

# Analyze a directory
nova analyze ~/Documents
nova analyze . --recursive

# Watch for new files (auto-organize)
nova watch ~/Downloads
nova watch ~/Downloads --live               # Actually move (not just preview)

# System info
nova system

# Find large files
nova large ~ --min-size 200

# Cleanup suggestions
nova cleanup

# Ask AI anything
nova ask "how much disk space am I using?"
nova ask "find all Python files modified today"

# Configuration
nova config
```

### Interactive Commands

Inside the Nova shell (`nova`):

| Command | Description |
|---------|-------------|
| `/organize <dir>` | Organize files |
| `/analyze <dir>` | Analyze directory |
| `/watch <dir>` | Watch for new files |
| `/system` | System information |
| `/processes` | Top processes |
| `/disks` | Disk usage |
| `/large [dir]` | Find large files |
| `/cleanup` | Cleanup suggestions |
| `/clear` | Clear AI conversation |
| `/config` | Show configuration |
| `/help` | Show all commands |
| `/quit` | Exit |

Or just type naturally — Nova understands plain English.

## Configuration

Config is stored at `~/.nova/config.yaml`:

```yaml
ai:
  model: claude-sonnet-4-20250514
  max_tokens: 4096
organizer:
  dry_run: false
watch:
  directories:
    - ~/Downloads
```

Organization rules are at `~/.nova/organize_rules.yaml` — customize which file types go where.

## File Categories

Nova organizes files into these default categories:

| Category | Extensions | Folder |
|----------|-----------|--------|
| Documents | pdf, doc, txt, md, epub... | Documents/ |
| Images | jpg, png, gif, svg, webp... | Pictures/ |
| Videos | mp4, mkv, avi, mov... | Videos/ |
| Audio | mp3, wav, flac, aac... | Music/ |
| Code | py, js, ts, go, rs, java... | Code/ |
| Data | csv, json, xml, sql, xlsx... | Data/ |
| Archives | zip, tar, gz, rar, 7z... | Archives/ |
| Installers | exe, dmg, deb, rpm... | Installers/ |
| Fonts | ttf, otf, woff... | Fonts/ |
| Design | psd, ai, sketch, fig... | Design/ |

## Requirements

- Python 3.10+
- Anthropic API key (for AI features — organizer works without it)
