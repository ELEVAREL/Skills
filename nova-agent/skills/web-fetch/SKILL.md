---
name: web-fetch
version: 0.1.0
description: Fetch URLs and extract readable text so Nova can read the web without a browser
author: Nova Agent
tags: [web, http, research]
tools: [http_get, web_read]
triggers: [fetch, url, http, website, scrape, read page]
personas: [researcher, nova-default]
---

# Web Fetch

Lightweight HTTP + HTML-to-text tools so Nova can grab pages without needing a full
browser automation stack.

- **http_get** — raw GET with size caps and redirect limits
- **web_read** — GET then strip HTML tags down to plaintext (first ~12k chars)

Only `http://` and `https://` are allowed; `file://`, `ftp://`, and private IPs are refused.
