"""Nova tunnel — expose the local gateway publicly with zero port forwarding.

Currently wraps `cloudflared` in quick-tunnel mode, which gives every user a
free `*.trycloudflare.com` HTTPS URL without requiring a Cloudflare account.
No domain, no DNS, no auth setup — just a binary and a PID.
"""

from nova.tunnel.cloudflare import CloudflareTunnel

__all__ = ["CloudflareTunnel"]
