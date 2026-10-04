# SmartDrain Project Status Report Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a bright, modern, evidence-backed HTML dashboard that explains SmartDrain's composition, current stage, completed work, and next roadmap to non-technical readers.

**Architecture:** Create one self-contained semantic HTML document with embedded CSS and no external runtime dependency. Reuse two existing project screenshots by relative path, derive every status statement from repository evidence, and distinguish MVP implementation from the later enhancement roadmap.

**Tech Stack:** HTML5, CSS3, existing PNG screenshots, PowerShell-based static checks

## Global Constraints

- Use a bright white and cool-gray visual system with teal and blue accents.
- The report must remain understandable to non-technical readers.
- Percentages are qualitative evidence summaries, not production-readiness scores.
- Do not add dependencies, external CDNs, or application JavaScript.
- Do not modify frontend, backend, AI service, infrastructure, or environment settings.
- Support desktop, mobile, reduced motion, and printing.

---

### Task 1: Build the single-page report

**Files:**
- Create: `docs/project-status-report.html`
- Reference: `frontend/docs/images/main-page.png`
- Reference: `frontend/docs/images/detail-page.png`

**Interfaces:**
- Consumes: repository evidence summarized in `docs/superpowers/specs/2026-08-01-project-status-report-design.md`
- Produces: a standalone HTML report reachable through section anchor links

- [ ] **Step 1: Create semantic document structure**

Create `header`, sticky `nav`, `main`, named `section` elements, and `footer`. Include Hero, composition flow, screenshots, domain progress, timeline, roadmap, status board, next priorities, and evidence notes.

- [ ] **Step 2: Add the light visual system**

Embed CSS variables for white, cool-gray, navy, teal, and blue. Add responsive grids, progress rings using `conic-gradient`, accessible progress bars, timeline cards, status badges, screenshot frames, print styles, and reduced-motion handling.

- [ ] **Step 3: Add evidence-backed content**

Use these headline values exactly: MVP code evidence 75%, enhancement-roadmap execution 8%, Phase 0 50%. Use the phase values `50, 0, 0, 0, 0, 0` and domain values `75, 75, 50, 75, 25, 0`. State that the values are qualitative summaries and that recent full E2E execution was not performed for this report. Use the master plan's Phase names and order exactly: 기준 확정과 코드 크로스체크; 인증·권한과 기준정보 관리; 작업 요청과 현장 처리; MQTT와 이벤트 신뢰성; 일일 보고서와 LangGraph; 운영 모니터링과 실제 연동.

- [ ] **Step 4: Check local assets and anchors**

Run:

```powershell
$html = Get-Content -Raw docs\project-status-report.html
@('../frontend/docs/images/main-page.png','../frontend/docs/images/detail-page.png') | ForEach-Object { Test-Path (Join-Path 'docs' $_) }
[regex]::Matches($html, 'href="#([^"]+)"') | ForEach-Object { $_.Groups[1].Value } | ForEach-Object { $html -match ('id="' + [regex]::Escape($_) + '"') }
```

Expected: every asset and anchor check returns `True`.

### Task 2: Verify content and rendering

**Files:**
- Verify: `docs/project-status-report.html`
- Verify: `docs/superpowers/specs/2026-08-01-project-status-report-design.md`

**Interfaces:**
- Consumes: completed HTML report
- Produces: verified desktop/mobile presentation and a clean Git diff

- [ ] **Step 1: Check percentage arithmetic and claim markers**

Run:

```powershell
$phases = 50,0,0,0,0,0
($phases | Measure-Object -Average).Average
rg -n "75%|8%|50%|최근 전체 E2E|실제 CCTV|인증·권한|MQTT|일일 보고서" docs\project-status-report.html
```

Expected: average is approximately `8.33`; the displayed aggregate is rounded to `8%`; every required qualification appears in the report.

- [ ] **Step 2: Render desktop and mobile screenshots**

Open the local HTML in an available browser automation environment. Capture one desktop viewport and one mobile viewport, then inspect overflow, text clipping, image loading, progress rings, bar labels, and navigation.

- [ ] **Step 3: Validate the final diff**

Run:

```powershell
# These files are new and therefore are not inspected by plain `git diff --check`.
$newDocs = @(
  'docs/project-status-report.html',
  'docs/superpowers/specs/2026-08-01-project-status-report-design.md',
  'docs/superpowers/plans/2026-08-01-project-status-report.md'
)
$whitespaceErrors = @()
foreach ($path in $newDocs) {
  $lineNumber = 0
  Get-Content $path | ForEach-Object {
    $lineNumber++
    if ($_ -match '[ \t]+$') { $whitespaceErrors += "${path}:${lineNumber}: trailing whitespace" }
  }
  $bytes = [System.IO.File]::ReadAllBytes((Resolve-Path $path))
  if ($bytes.Length -eq 0 -or $bytes[-1] -ne 10) { $whitespaceErrors += "${path}: missing final newline" }
}
$whitespaceErrors
if ($whitespaceErrors.Count -gt 0) { throw 'Whitespace validation failed.' }
git diff --check
git status --short
git diff -- docs/project-status-report.html docs/superpowers/specs/2026-08-01-project-status-report-design.md docs/superpowers/plans/2026-08-01-project-status-report.md
```

Expected: `$whitespaceErrors` is empty, every new documentation file ends with a newline, `git diff --check` reports no tracked-file whitespace errors, and only the intended documentation files are changed.
