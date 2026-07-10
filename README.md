# Product Dashboard

> **Work in progress** — active development, v0.1

A product portfolio dashboard built with [Reflex](https://reflex.dev) (Python → React, no JS files).  
Designed to demonstrate product thinking across the full SDLC — from discovery to monitoring.

[README на русском](README_RU.md)

---

## What is this

An interactive dashboard that shows a real software project through the lens of every product role:  
PM, BA, SA, Designer, PA, Dev, QA, Growth, and more.

The dashboard supports **3 project modes** switchable at runtime:
- **Motif Demo** — a fictional product team with generated Jira-like data
- **Knowledge Pipeline** — a real solo AI project (YouTube → Obsidian notes via Claude API)
- **Product Dashboard** — this dashboard itself, shown as a product project with real sprint history

**North Star:** *"A recruiter understands the product context without any explanation."*

---

## What's ready now

**Technical foundation**
- 17 SDLC tabs: About, Practices & Rules, Kanban, Backlog, Roadmap, Overview/PM, Research, Analytics, Architecture, Requirements, Design, Design System, Dev & Pipeline, Quality, Release, Monitoring, Growth
- All tabs are built and navigable (no empty pages)
- 3 project modes with runtime switching via dropdown
- Design tokens in W3C format (`design_tokens.json`), synced with Figma Tokens Studio
- Hand-authored Jira mock data: 88 tasks with full sprint history, epics, decision notes
- Reactive filters in Backlog (squad, type, sprint, epic, OKR)
- Accordion navigation: Design System nested under Design
- `USER_STORIES.md` — 17 roles × 100+ user stories

**Real project data (Knowledge Pipeline mode)**
- Pipeline metrics: notes created, processing time, token usage
- Vault snapshot: folder structure, note count
- Architecture Decision Records from real README
- Quality checklist from real security review

---

## What's in progress

- [ ] Figma files: wireframes and hi-fi mockups (design process visible in code, not yet in Figma)
- [ ] GitHub release with public URL (currently local only)
- [ ] Recruiter onboarding: tooltips, coach marks
- [ ] Design Process tab: journey map, HMW, user flow
- [ ] Comic/scenario: 2-week sprint story with role diaries
- [ ] Framer portfolio site with link to this dashboard

---

## How to run locally

**Requirements:** Python 3.11+, Node.js 18+

```bash
git clone https://github.com/plaidshirtfemme/product-dashboard.git
cd dashboard-product
pip install -r requirements.txt
reflex run
```

Open [http://localhost:3000](http://localhost:3000)

> **Note:** The first run takes 1–2 minutes — Reflex compiles the frontend.  
> Subsequent runs are faster.

---

## Tech stack

| Layer | Technology |
|-------|-----------|
| Framework | [Reflex](https://reflex.dev) 0.9.x — Python → React |
| UI components | Radix UI via Reflex |
| Design tokens | W3C Design Tokens format |
| Data | Hand-authored Jira mock + real project extract |
| Python | 3.11+ |

---

## Project structure

```
dashboard_product/
├── dash_app/
│   ├── pages/          # one file per tab
│   ├── components/     # shared UI components
│   ├── states/         # Reflex state (NavState, ProjectState, BacklogState…)
│   ├── data/           # mock data, adapter, real project extract
│   └── tokens/         # design tokens → Python
├── scripts/            # vault snapshot update script
├── wiki/               # role diaries, PM notes
├── USER_STORIES.md     # 17 roles × 100+ user stories
└── rxconfig.py
```

---

*Built by Guzel Karimova · Product Designer & PM · 2026*
