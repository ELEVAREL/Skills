---
name: screenshot
version: 0.1.0
description: Capture screen or window screenshots to disk (cross-platform)
author: Nova Agent
tags: [screen, capture, vision]
tools: [take_screenshot]
triggers: [screenshot, screen grab, capture screen]
personas: [nova-default, automator]
---

# Screenshot

Captures the primary screen to a PNG file under `~/.nova/screenshots/`.
Uses the `pillow`/`mss` stack when available and falls back to OS-native tools.

- Windows: uses `mss` (via pip) or PowerShell's `Add-Type` fallback
- macOS: falls back to `screencapture`
- Linux: falls back to `gnome-screenshot` or `scrot`
