"""Nova Gateway — HTTP control plane so channels can talk to Nova's brain.

The gateway is just a control surface; the *product* is the persona + skills.
This module exposes:

- POST /v1/chat            → run a chat turn (persona-aware, tool-enabled)
- GET  /v1/personas        → list available personas
- POST /v1/personas/active → switch active persona
- GET  /v1/skills          → list loaded skills
- POST /v1/skills/toggle   → enable/disable a skill
- GET  /v1/memory          → list memories
- POST /v1/memory          → add a memory
- GET  /healthz            → liveness

Auth: optional bearer token from ~/.nova/gateway.token (auto-generated on first run).
"""

from nova.gateway.server import GatewayServer, start_gateway, stop_gateway

__all__ = ["GatewayServer", "start_gateway", "stop_gateway"]
