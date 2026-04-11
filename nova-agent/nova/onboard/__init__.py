"""Nova onboarding wizard — install-to-textable in under 5 minutes.

This is the killer feature that makes Nova a one-time-buy product: a single
`nova onboard` command that walks the user from zero to "my phone can text
my computer" without manual config.

Flow:
    1. Verify Python + deps
    2. Prompt for Anthropic API key (or reuse ANTHROPIC_API_KEY env)
    3. Start the local gateway + pick a persona
    4. Walk through Telegram @BotFather → paste token → verify
    5. Spin up a Cloudflare Tunnel (public URL without port forwarding)
    6. Register the Telegram webhook → tunnel → local gateway
    7. Install Nova as an auto-start service (optional, OS-aware)
    8. Send a test message from the user's phone → confirm round-trip
"""

from nova.onboard.wizard import run_onboard

__all__ = ["run_onboard"]
