# Marketing Report — Elevare

Reusable system for producing full marketing reports and asset packages for Elevare clients.

## What this folder is for

Each client engagement produces:

1. A **marketing report** (strategy, market, competitors, content plan, growth roadmap)
2. A set of **marketing assets** (social graphics, content calendar, brand voice guide, campaign briefs)
3. Optional **implementation** (Google Business Profile, posting schedule, ad setup)

## Folder structure

```
marketing-report/
├── README.md              ← this file
├── TEMPLATE.md            ← blank report template (copy per client)
├── PROCESS.md             ← step-by-step research + delivery workflow
├── PRICING.md             ← pricing tiers and rationale
├── clients/               ← one subfolder per client
│   └── <client-slug>/
│       ├── report.md
│       ├── research-notes.md
│       └── assets/
└── FANTA-AFRICAN-HAIR-MARKETING-REPORT.md   ← first delivered report (reference)
```

## How to use

1. Copy `TEMPLATE.md` into `clients/<client-slug>/report.md`
2. Follow `PROCESS.md` to gather research
3. Fill in every section — never leave placeholder text
4. Generate matching graphics in `../social-media-graphics/` and copy finals into `clients/<client-slug>/assets/`
5. Export to PDF for client delivery

## Sister folders

- `../social-media-graphics/` — HTML templates for Instagram/TikTok posts
- `../skills/brand-voice/` — brand voice extraction workflow
- `../skills/content-engine/` — content calendar generation
