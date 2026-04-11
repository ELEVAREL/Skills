"""The onboard wizard — interactive, step-by-step, reversible."""

from __future__ import annotations

import json
import os
import platform
import time
import webbrowser
from pathlib import Path

from nova.config import DEFAULT_CONFIG_DIR, ensure_config_dir, load_config, save_config
from nova.utils.display import (
    banner, console, error, info, muted, section_header, success, warning,
)

ONBOARD_STATE = DEFAULT_CONFIG_DIR / "onboard.json"


def _load_state() -> dict:
    if ONBOARD_STATE.exists():
        try:
            return json.loads(ONBOARD_STATE.read_text())
        except json.JSONDecodeError:
            return {}
    return {}


def _save_state(state: dict) -> None:
    ensure_config_dir()
    ONBOARD_STATE.write_text(json.dumps(state, indent=2))


def _ask(prompt_text: str, default: str = "") -> str:
    suffix = f" [{default}]" if default else ""
    try:
        answer = input(f"  {prompt_text}{suffix}: ").strip()
    except (EOFError, KeyboardInterrupt):
        return ""
    return answer or default


def _confirm(prompt_text: str, default: bool = True) -> bool:
    hint = "Y/n" if default else "y/N"
    try:
        answer = input(f"  {prompt_text} [{hint}]: ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        return False
    if not answer:
        return default
    return answer in ("y", "yes")


def run_onboard() -> None:
    """Top-level wizard entry point."""
    banner()
    console.print()
    section_header("Nova Onboarding", icon="◆")
    muted("This wizard will set up Nova so you can text your computer from anywhere.")
    muted("You can re-run it any time to add channels or reconfigure.")
    console.print()

    state = _load_state()
    ensure_config_dir()

    steps = [
        ("api_key", step_api_key),
        ("persona", step_pick_persona),
        ("gateway", step_start_gateway),
        ("telegram", step_telegram_bot),
        ("tunnel", step_cloudflare_tunnel),
        ("webhook", step_register_webhook),
        ("service", step_install_service),
        ("test", step_test_round_trip),
    ]

    for name, fn in steps:
        console.print()
        try:
            result = fn(state)
        except KeyboardInterrupt:
            warning("\n  Interrupted — run `nova onboard` again to resume.")
            _save_state(state)
            return
        state[name] = result
        _save_state(state)
        if result.get("skipped"):
            muted(f"  ⋯ {name} skipped")
        elif result.get("ok"):
            success(f"  ✓ {name} done")
        else:
            error(f"  ✗ {name} failed: {result.get('error', 'unknown')}")
            if not _confirm("Continue anyway?", default=False):
                _save_state(state)
                return

    console.print()
    section_header("All set", icon="◆")
    success("Nova is live. Text your bot from your phone to chat.")
    muted("Run `nova gateway status` any time to verify it's reachable.")
    muted("Run `nova service status` to check the background service.")


# ─── Step 1: API key ─────────────────────────────────────────────────
def step_api_key(state: dict) -> dict:
    section_header("1. Anthropic API key", icon="①")
    existing = os.environ.get("ANTHROPIC_API_KEY", "")
    if existing:
        info(f"Found ANTHROPIC_API_KEY in environment ({existing[:10]}…)")
        if _confirm("Use this key?"):
            return {"ok": True, "source": "env"}

    muted("Get a key at https://console.anthropic.com/settings/keys")
    if _confirm("Open the console in your browser?"):
        try:
            webbrowser.open("https://console.anthropic.com/settings/keys")
        except Exception:
            pass

    key = _ask("Paste your Anthropic API key (starts with sk-ant-)")
    if not key or not key.startswith("sk-ant-"):
        return {"ok": False, "error": "no valid key provided", "skipped": not key}

    # Persist to ~/.nova/env so the service picks it up
    env_file = DEFAULT_CONFIG_DIR / "env"
    env_file.write_text(f"ANTHROPIC_API_KEY={key}\n")
    try:
        env_file.chmod(0o600)
    except OSError:
        pass
    os.environ["ANTHROPIC_API_KEY"] = key
    return {"ok": True, "source": "prompt", "env_file": str(env_file)}


# ─── Step 2: persona ─────────────────────────────────────────────────
def step_pick_persona(state: dict) -> dict:
    section_header("2. Default persona", icon="②")
    from nova.personas import get_persona_registry
    reg = get_persona_registry()
    personas = reg.list_all()

    if not personas:
        return {"ok": False, "error": "no personas found"}

    for i, p in enumerate(personas, 1):
        console.print(f"  [cyan]{i}[/]. [bold]{p.id}[/] — {p.description}")

    default_idx = next((i for i, p in enumerate(personas, 1) if p.id == "nova-default"), 1)
    choice = _ask(f"Pick a persona (1-{len(personas)})", str(default_idx))
    try:
        idx = int(choice) - 1
        if not 0 <= idx < len(personas):
            raise ValueError
    except ValueError:
        idx = default_idx - 1

    picked = personas[idx]
    reg.activate(picked.id)

    cfg = load_config()
    cfg.setdefault("onboard", {})["default_persona"] = picked.id
    save_config(cfg)

    return {"ok": True, "persona": picked.id}


# ─── Step 3: gateway ─────────────────────────────────────────────────
def step_start_gateway(state: dict) -> dict:
    section_header("3. Start the local gateway", icon="③")
    from nova.gateway import start_gateway
    try:
        gw = start_gateway(host="127.0.0.1", port=7878)
    except OSError as e:
        return {"ok": False, "error": f"gateway failed to bind: {e}"}
    info(f"Gateway listening on {gw.url}")
    muted(f"Token file: {Path.home() / '.nova' / 'gateway.token'}")
    return {"ok": True, "url": gw.url}


# ─── Step 4: Telegram bot ────────────────────────────────────────────
def step_telegram_bot(state: dict) -> dict:
    section_header("4. Telegram bot", icon="④")
    if not _confirm("Set up Telegram as your messaging channel?"):
        return {"skipped": True, "ok": True}

    muted("1. Open Telegram and message @BotFather")
    muted("2. Send /newbot, pick a name and a username ending in _bot")
    muted("3. Copy the token BotFather sends you (looks like 123:ABC...)")
    if _confirm("Open @BotFather in your browser now?"):
        try:
            webbrowser.open("https://t.me/BotFather")
        except Exception:
            pass

    token = _ask("Paste your bot token")
    if not token or ":" not in token:
        return {"skipped": True, "ok": True}

    # Save to env file so the service can pick it up
    env_file = DEFAULT_CONFIG_DIR / "env"
    existing = env_file.read_text() if env_file.exists() else ""
    lines = [l for l in existing.splitlines() if not l.startswith("TELEGRAM_BOT_TOKEN=")]
    lines.append(f"TELEGRAM_BOT_TOKEN={token}")
    env_file.write_text("\n".join(lines) + "\n")
    os.environ["TELEGRAM_BOT_TOKEN"] = token

    # Verify the token by hitting getMe
    from nova.channels.telegram import TelegramChannel
    ch = TelegramChannel(token=token)
    result = ch._api("getMe")  # noqa: SLF001
    if not result.get("ok"):
        return {"ok": False, "error": f"Telegram rejected the token: {result.get('error', 'unknown')}"}

    bot_info = result.get("result", {})
    bot_username = bot_info.get("username", "your bot")
    success(f"Verified bot @{bot_username}")
    return {"ok": True, "token_preview": token[:12] + "...", "username": bot_username}


# ─── Step 5: Cloudflare Tunnel ───────────────────────────────────────
def step_cloudflare_tunnel(state: dict) -> dict:
    section_header("5. Public URL (Cloudflare Tunnel)", icon="⑤")
    telegram_set = state.get("telegram", {}).get("ok") and not state.get("telegram", {}).get("skipped")
    if not telegram_set:
        muted("Skipped — no channel needs a public URL yet")
        return {"skipped": True, "ok": True}

    from nova.tunnel import CloudflareTunnel
    tunnel = CloudflareTunnel()
    if not tunnel.is_installed():
        warning("cloudflared binary not found")
        if not _confirm("Try to install cloudflared automatically?"):
            return {"ok": False, "error": "cloudflared not installed"}
        installed = tunnel.install()
        if not installed.get("ok"):
            return {"ok": False, "error": installed.get("error", "install failed")}
        success("cloudflared installed")

    info("Starting tunnel to localhost:7878...")
    result = tunnel.start(local_port=7878)
    if not result.get("ok"):
        return {"ok": False, "error": result.get("error", "tunnel failed")}

    public_url = result["url"]
    success(f"Public URL: {public_url}")
    muted("This URL points at your local Nova gateway with full HTTPS.")
    return {"ok": True, "url": public_url, "pid": result.get("pid")}


# ─── Step 6: Telegram webhook ────────────────────────────────────────
def step_register_webhook(state: dict) -> dict:
    section_header("6. Register Telegram webhook", icon="⑥")
    tg = state.get("telegram", {})
    tun = state.get("tunnel", {})
    if tg.get("skipped") or tun.get("skipped") or not tun.get("url"):
        return {"skipped": True, "ok": True}

    token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    if not token:
        return {"ok": False, "error": "no telegram token in environment"}

    from nova.channels.telegram import TelegramChannel
    ch = TelegramChannel(token=token)

    # The tunnel already forwards /* to the gateway; we mount webhook at /v1/telegram
    webhook_url = tun["url"].rstrip("/") + "/v1/telegram"

    # Nova gateway needs to expose this route — we'll do that in the gateway module
    result = ch._api("setWebhook", {"url": webhook_url})  # noqa: SLF001
    if not result.get("ok"):
        return {"ok": False, "error": f"setWebhook failed: {result.get('description', result.get('error', 'unknown'))}"}

    success(f"Webhook registered: {webhook_url}")
    return {"ok": True, "webhook_url": webhook_url}


# ─── Step 7: background service ──────────────────────────────────────
def step_install_service(state: dict) -> dict:
    section_header("7. Install as background service", icon="⑦")
    muted("This lets Nova run 24/7 without keeping a terminal open.")
    if not _confirm("Install Nova as an auto-start service?", default=True):
        return {"skipped": True, "ok": True}

    from nova.service import install_service, get_platform_installer
    installer = get_platform_installer()
    if installer is None:
        return {"ok": False, "error": f"no installer for {platform.system()}"}

    result = install_service()
    if not result.get("ok"):
        return {"ok": False, "error": result.get("error", "install failed")}

    success(f"Service installed ({result.get('method', '?')})")
    muted("Manage it with: nova service [start|stop|status|uninstall]")
    return {"ok": True, "method": result.get("method")}


# ─── Step 8: round-trip test ─────────────────────────────────────────
def step_test_round_trip(state: dict) -> dict:
    section_header("8. Round-trip test", icon="⑧")
    tg = state.get("telegram", {})
    if tg.get("skipped") or not tg.get("ok"):
        muted("Skipped — no channel configured")
        return {"skipped": True, "ok": True}

    username = tg.get("username", "your bot")
    info(f"Open Telegram and send a message to @{username}")
    muted("Nova should reply within a few seconds.")
    if _confirm("Did you receive a reply?"):
        return {"ok": True}
    muted("  Check `nova gateway status` and `nova service status` if not.")
    return {"ok": False, "error": "no round-trip confirmed"}
