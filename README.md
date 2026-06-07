# Career Advisor Skill

<p align="right">
  <a href="README.md">中文</a> | <a href="README.en.md">English</a>
</p>

> 一个面向 AI Agent 的开源职业顾问 skill，帮助用户创建简历、渲染 PDF、补全经历细节，并准备技术面试。

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Version: 1.0.0](https://img.shields.io/badge/version-1.0.0-blue.svg)](CHANGELOG.md)
[![Agent Skills](https://img.shields.io/badge/agent--skills-compatible-green.svg)](https://agentskills.io/home)

---

## 它能做什么

这个 skill 会把你的 AI Agent 变成一个 **Career Advisor（职业顾问）**，内置 4 个核心工作流：

| 工作流 | 用途 | 输出 |
|---|---|---|
| **W1 — 新建简历** | 收集 5 类基础信息 + 套用模板 -> 写出简历 | `.md` 简历初稿 |
| **W2 — 渲染 PDF** | 套用模板 + 按语言分支处理 -> 渲染 1 页 A4 PDF | `CV-<name>.pdf` |
| **W3 — 问答式补全** | 逐项追问 `[待补]` / `[TBD]` 字段 -> 实时写回 | 更新后的 `.md` 简历 |
| **W4 — 面试题生成** | 基于 JD + 行业 + 简历生成 10-15 道技术面试问答 | 面试 Q&A `.md` 文件 |

### 核心特性

- **内置中英文两个语言分支**：
  - **英文**：1 页 A4 美式简历，不放照片
  - **中文**：1 页 A4 简历，嵌入证件照（必需；仅接受白色/蓝色/灰色背景）
- **防止编造的硬约束**：不会替用户虚构数字、公司或成果；未知字段统一标记为 `[待补]` / `[TBD]`
- **JD 关键词对齐**：目标 JD 的高频关键词需要在 Summary / Experience / Skills 中达到至少 70% 覆盖
- **简历精简原则**：弱相关经历会被删减；课程作业不包装成项目；本科论文标记为论文而不是 “Publications”
- **数字/代码消歧**：在工业、制造业语境下，独立出现的 4 位及以上数字优先视为 **产品代码**，而不是数量
- **模板驱动**：随包提供中英文 starter templates；PDF 渲染工具可自行选择（reportlab / weasyprint / pandoc 等）

---

## 安装

### 从 `.skill` 文件安装

```bash
# 解压到你的 Agent skills 目录
unzip career-advisor-skill.skill -d ~/.your-agent/skills/

# 或者只抽取为 career-advisor 文件夹结构
unzip -j career-advisor-skill.skill -d ~/.your-agent/skills/career-advisor/
```

skill 目录结构如下：

```text
career-advisor/
├── SKILL.md
├── assets/
│   └── templates/
│       ├── resume-template-en.md
│       └── resume-template-zh.md
├── references/    # 默认空目录，可放自己的深度参考文档
└── scripts/       # 默认空目录，可放自己的渲染脚本
```

### 从源码安装

```bash
git clone https://github.com/ietigerjue/career-advisor-skill.git
cp -r career-advisor-skill/ ~/.your-agent/skills/career-advisor/
```

---

## 使用方式

安装后，当用户使用下面这些触发词时，skill 会被激活：

**英文**：`career advisor`、`job search`、`resume`、`new resume`、`generate PDF`、`technical interview`、`mock interview`、`interview questions`

**中文**：「职业顾问」「求职」「简历」「新建简历」「出 PDF」「生成简历」「技术面」「面试题」

### 快速开始

```text
You: "Help me build a new resume for a market research intern role in English"

Skill (W1): "Great. I need 5 baseline fields. Let's start with contact info:
             name, email, phone, city, and LinkedIn (optional)."

You: [提供信息]

Skill (W1): "Got it. Next: education — school, major, degree, dates, GPA if >3.5."
...
```

### 触发词 -> 工作流映射

| 用户说 | 工作流 |
|---|---|
| `new resume` / `build my resume` / `use this template` | **W1** |
| `export PDF` / `render resume` / `generate PDF` | **W2** |
| `fill in` / `add more` / `expand` / `too thin` | **W3** |
| `interview questions` / `10-15 questions` / `mock interview` | **W4** |

---

## 数据目录

skill 会期望或创建以下目录，路径相对于 Agent 写入文件的位置：

```text
career-advisor-data/
├── resume-library/         # W1 输出：简历草稿 v1、v2、v3...
├── JD-library/             # W4 输入：已保存的目标 JD
├── interview-questions/    # W4 输出：10-15 道面试 Q&A 文件
├── templates/              # 自定义模板，可与 assets/templates/ 并存
└── photo/                  # 一张证件照文件，仅中文简历需要
```

你可以使用任意路径，只要告诉 Agent 你的偏好目录即可。

---

## 这个 skill 不包含什么

这个 skill 故意保持聚焦，因此 **不包含**：

- **PDF 渲染脚本**：请搭配你偏好的 `markdown -> PDF` 工具使用，例如 reportlab、weasyprint、pandoc、LaTeX 等。随包模板可配合任意渲染方案。
- **照片背景自动移除**：该流程明确不在 scope 内。如果用户照片背景过暗、偏暖或杂乱，skill 会把问题交还给用户，并提供两个选项：更换背景或重新拍摄。
- **HR 数据 / 公司情报 / 薪资基准**：skill 会基于简历 + JD 生成面试题，不使用私有数据。
- **中英文之外的多语言**：如需其他语言，可自行添加模板。

---

## 自定义

### 添加新模板

1. 在 `assets/templates/`（或你的自定义 `templates/` 目录）下创建 `resume-template-<lang>-vN.md`
2. 添加包含 `template_id`、`language`、`embeds_photo`、`sections` 的 frontmatter
3. W1 工作流会发现该模板并提供给用户选择

示例 frontmatter：

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

### 添加辅助脚本

把可执行脚本放进 `scripts/`，并在 `SKILL.md` 或模板中用相对路径引用。skill 不会自动执行脚本，Agent 会根据工作流需要调用。

---

## 贡献

欢迎提交 issues 和 PR。请注意：

1. 如果是行为变化，请先开 issue
2. 保持 `SKILL.md` 小于 30 KB，方便快速加载
3. 示例中不要包含个人数据、真实姓名或真实公司信息
4. 跑一遍脱敏检查清单（无 PII / 无内部路径 / 无专有数据）

---

## 许可证

MIT — 见 [LICENSE](LICENSE)。

---

## 致谢

- 格式规范：[agentskills.io](https://agentskills.io/home)
- 灵感来自更广泛的 agent-skills 生态
- 基于真实求职工作流构建并验证
