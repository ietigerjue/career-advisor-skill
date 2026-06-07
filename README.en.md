# Career Advisor Skill

<p align="right">
  <a href="README.md">中文</a> | <a href="README.en.md">English</a>
</p>

> An open-source skill for AI agents that helps users create resumes, render PDFs, fill in
> experience details, and prep for technical interviews.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Version: 1.1.0](https://img.shields.io/badge/version-1.1.0-blue.svg)](CHANGELOG.md)
[![Agent Skills](https://img.shields.io/badge/agent--skills-compatible-green.svg)](https://agentskills.io/home)

---

## What It Does

This skill turns your AI agent into a **career advisor** with 4 core workflows:

| Workflow | Purpose | Output |
|---|---|---|
| **W1 — New Resume** | Collect 5 baseline fields + apply template → write resume | `.md` resume draft |
| **W2 — Render PDF** | Apply template + language branch → render 1-page A4 PDF | `CV-<name>.pdf` |
| **W3 — Q&A Fill-in** | Chase `[待补]` / `[TBD]` fields one by one → write back live | Updated `.md` resume |
| **W4 — Interview Questions** | Generate 10-15 technical interview Q&A from JD + industry + resume | Q&A `.md` file |

### Key Features

- **Two language branches** out of the box:
  - **English**: 1-page A4 US-style, no photo
  - **Chinese**: 1-page A4, embeds a portrait photo (mandatory, white/blue/gray background only)
- **Hard guardrails against fabrication**: never invents numbers, companies, or outcomes for
  the user — unknown fields are marked `[待补]` / `[TBD]`
- **JD keyword alignment**: target-JD high-frequency words must hit ≥70% in
  Summary / Experience / Skills
- **Trimming principles**: weakly related experiences get cut, course assignments aren't padded
  as projects, undergraduate theses are marked as theses (not "Publications")
- **Number/code disambiguation**: standalone 4+ digit numbers in industrial / manufacturing
  context are treated as **product codes**, not quantities
- **Template-based + script-assisted**: ships with starter templates, a Markdown-to-PDF helper,
  and a local photo background removal helper

---

## Installation

### From the `.skill` file

```bash
# Unzip into your agent's skills directory
unzip career-advisor-skill.skill -d ~/.your-agent/skills/

# Or extract just the folder structure
unzip -j career-advisor-skill.skill -d ~/.your-agent/skills/career-advisor/
```

The skill layout is:

```text
career-advisor/
├── SKILL.md
├── assets/
│   └── templates/
│       ├── resume-template-en.md
│       └── resume-template-zh.md
├── requirements-optional.txt
├── references/    # (empty by default — add your own deep-dive docs)
└── scripts/
    ├── render_resume_pdf.py
    ├── remove_photo_background.py
    └── verify_scripts.py
```

### From source

```bash
git clone https://github.com/ietigerjue/career-advisor-skill.git
cp -r career-advisor-skill/ ~/.your-agent/skills/career-advisor/
```

---

## Helper Scripts

The skill includes optional local helper scripts under `scripts/`. They do not call remote
services and they do not upload photos or resume content.

Install optional dependencies as needed:

```bash
pip install -r requirements-optional.txt
```

For the photo helper, use Python 3.11-3.13 because `rembg` may not support newer Python
versions yet. PDF rendering can still use the built-in `simple` backend without installing
optional dependencies.

### Render Markdown to PDF

```bash
python scripts/render_resume_pdf.py resume-library/resume_v2_market_research.md resume-library/CV-Name.pdf --language en

python scripts/render_resume_pdf.py resume-library/resume_v2_cn.md resume-library/CV-Name.pdf --language zh --photo photo/portrait-clean.png
```

`render_resume_pdf.py` supports:

- `--backend auto` (default): tries WeasyPrint, ReportLab, Pandoc, then the dependency-free simple backend
- `--backend weasyprint`: best HTML/CSS fidelity
- `--backend reportlab`: offline Python fallback; use `--font path/to/CJK.ttf` for Chinese
- `--backend pandoc`: uses local Pandoc and the selected PDF engine
- `--backend simple`: no dependencies; basic English draft output only, no photo embedding

Chinese resumes require `--photo` unless `--allow-missing-photo` is used for drafts.

### Remove Photo Background

```bash
python scripts/remove_photo_background.py photo/portrait.jpg photo/portrait-clean.png --background white
```

Supported backgrounds: `white`, `light-blue`, `light-gray`, `transparent`, or a custom hex color
like `#ffffff`. The script writes a new file and refuses to overwrite the source unless `--force`
is explicitly provided.

The first `rembg` run may download its segmentation model into the local user cache. The image
itself is processed locally and is not uploaded by this script.

### Verify Scripts

```bash
python scripts/verify_scripts.py
```

This runs syntax checks, CLI `--help` smoke tests, and safe no-argument behavior checks without
installing optional dependencies.

---

## Usage

Once installed, the skill activates when the user uses any of these trigger phrases:

**English**: "career advisor", "job search", "resume", "new resume", "generate PDF",
"technical interview", "mock interview", "interview questions"

**Chinese**: 「职业顾问」「求职」「简历」「新建简历」「出 PDF」「生成简历」「技术面」「面试题」

### Quick start

```text
You: "Help me build a new resume for a market research intern role in English"

Skill (W1): "Great. I need 5 baseline fields. Let's start with contact info:
             name, email, phone, city, and LinkedIn (optional)."

You: [provide details]

Skill (W1): "Got it. Next: education — school, major, degree, dates, GPA if >3.5."
...
```

### Trigger phrase → workflow mapping

| User says | Workflow |
|---|---|
| "new resume" / "build my resume" / "use this template" | **W1** |
| "export PDF" / "render resume" / "generate PDF" | **W2** |
| "fill in" / "add more" / "expand" / "too thin" | **W3** |
| "interview questions" / "10-15 questions" / "mock interview" | **W4** |

---

## Data Layout

The skill expects (or creates) the following directories relative to wherever the agent writes:

```text
career-advisor-data/
├── resume-library/         # W1 output (resume drafts: v1, v2, v3…)
├── JD-library/             # W4 input (target JDs you've saved)
├── interview-questions/    # W4 output (10-15 Q&A files)
├── templates/              # Custom templates (in addition to assets/templates/)
└── photo/                  # One portrait photo file (Chinese resumes only)
```

You can use any path — just point the agent at your preferred location.

---

## What's NOT in this skill

This skill is intentionally focused. It does **not** include:

- **Bundled binary render engines** — high-fidelity output uses optional local dependencies such
  as WeasyPrint, ReportLab, Pandoc, Pillow, and rembg. Install only what you need.
- **Remote photo processing** — background removal is local-only; no upload service is used.
- **HR data / company intel / salary benchmarks** — the skill generates interview questions
  based on the resume + JD, not on proprietary data.
- **Multi-language beyond Chinese + English** — add your own template if needed.

---

## Customization

### Adding a new template

1. Create `resume-template-<lang>-vN.md` under `assets/templates/` (or your custom `templates/` dir)
2. Add frontmatter with `template_id`, `language`, `embeds_photo`, `sections`
3. The skill will discover and offer it to the user on W1

Example frontmatter:

```yaml
---
name: French Resume Template
description: 1-page French-style CV with photo.
template_id: resume-template-fr
language: fr
embeds_photo: true
sections: [etat_civil, formation, experience, competences]
---
```

### Adding helper scripts

Put additional executable scripts in `scripts/` and reference them by relative path in the
SKILL.md or templates. The skill doesn't auto-execute scripts — agents invoke them based on
workflow needs.

---

## Contributing

Issues and PRs welcome. Please:

1. Open an issue first if it's a behavior change
2. Keep SKILL.md under 30 KB for fast loading
3. Don't include personal data, real names, or real company info in examples
4. Run the desensitization checklist (no PII / no internal paths / no proprietary data)

---

## License

MIT — see [LICENSE](LICENSE).

---

## Acknowledgments

- Format spec: [agentskills.io](https://agentskills.io/home)
- Inspired by the broader agent-skills ecosystem
- Built and battle-tested in real job-search workflows
