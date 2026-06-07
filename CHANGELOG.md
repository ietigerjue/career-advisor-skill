# Changelog

All notable changes to this skill are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] — 2026-06-07

### Added
- **Markdown-to-PDF helper**: `scripts/render_resume_pdf.py` with WeasyPrint, ReportLab,
  Pandoc, and dependency-free simple backend options
- **Photo background cleanup helper**: `scripts/remove_photo_background.py` for local-only
  portrait background removal and white / light-blue / light-gray replacement
- **Script verification harness**: `scripts/verify_scripts.py`
- **Optional dependency list**: `requirements-optional.txt`
- **Bilingual README docs** for installing and running the helper scripts

### Changed
- **W2 PDF rendering protocol** now points to the bundled helper script instead of requiring
  users to bring their own render script
- **Photo background protocol** now allows local auto-removal with user approval while still
  preserving the original photo

---

## [1.0.0] — 2024-12-XX

### Added
- Initial public release
- **4 workflows** (W1-W4): new resume, render PDF, Q&A fill-in, technical interview questions
- **Two starter templates**:
  - `assets/templates/resume-template-en.md` (English, no photo, US-style)
  - `assets/templates/resume-template-zh.md` (Chinese, embeds photo, 3-section layout)
- **Trimming principles**: weakly related experiences cut, course assignments ≠ projects,
  undergraduate theses marked as theses (not Publications)
- **Number/code disambiguation rule**: standalone 4+ digit numbers in industrial context are
  treated as product codes, not quantities
- **Photo background rule**: Chinese resumes require white/blue/gray background; agent
  returns problem to user with replace/retake options
- **Anti-fabrication guardrail**: unknown fields marked `[待补]` / `[TBD]`, never invented
- **JD keyword alignment**: target-JD high-frequency words must hit ≥70%
- **Per-role question distribution** for W4 (R&D, Technical Sales, Market Research, General)
- **200-400 word answer rule** for W4 (no perfunctory one-liners)
- **STAR structure** required for W4 scenario case answers

### Design Decisions
- **Operation-style role**, not cheerleader: direct, data-driven, focused, actionable
- **No PDF render script bundled**: pair with your preferred `md → PDF` tool
- **No photo background removal**: explicitly out of scope
- **No multi-language beyond Chinese + English**: bring your own template if needed

### Privacy & Desensitization
- All identifying information from the author's personal workflow has been removed
- No real company names, project names, or personal data
- Generic placeholder names (`[Name]`, `[University Name]`, etc.) throughout
- Designed for safe public distribution

---

## Pre-1.0 (Author's Internal History)

For transparency, here's the upstream evolution that led to v1.0.0:

- **v0.x — Internal experimental**: 6-workflow "advisor-style" version with training plans
  (later removed as over-engineered for actual use)
- **v1.x — First simplification**: Reduced to 4 core workflows (W1-W4), operation-style
- **v2.x — Cross-platform fork**: 3 platform-specific versions (Hermes / Claude Code / Codex)
  to address loading-context differences
- **v3.x — Protocol hardening**: 5-section English template + 3-section Chinese template
  + 5-step W1 data collection + W3-vs-W1 gap-reporting distinction + photo background rule
- **v4 protocol — Photo rule simplification**: dropped the 5-step background-removal decision
  tree (rembg / ImageMagick / PIL ellipse mask). New rule: agent never auto-removes
  backgrounds; user is given two options (replace background / retake). This is the rule
  that ships in v1.0.0.
- **Public release prep**: desensitized, packaged as `.skill` file, documented with README +
  CHANGELOG, GitHub-published

[Unreleased]: https://github.com/ietigerjue/career-advisor-skill/compare/v1.1.0...HEAD
[1.1.0]: https://github.com/ietigerjue/career-advisor-skill/releases/tag/v1.1.0
[1.0.0]: https://github.com/ietigerjue/career-advisor-skill/releases/tag/v1.0.0
