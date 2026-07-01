# Stitch UI Refresh P2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend the approved Stitch-inspired UI refresh to the remaining knowledge, document, assistant debug, and settings pages without changing backend behavior.

**Architecture:** Keep all current routes, stores, services, API contracts, forms, and permission boundaries intact. Apply the P0/P1 visual system through existing Vue class names and scoped template copy enhancements only, using `frontend/src/assets/main.css` as the primary integration point.

**Tech Stack:** Vue 3, Vite, TypeScript, CSS, existing Material Symbols icons, existing REST services.

---

### Task 1: Knowledge And QA Pages

**Files:**
- Modify: `frontend/src/assets/main.css`

- [x] Align `knowledge-page`, `knowledge-overview-header`, `knowledge-actions`, `knowledge-metric-grid`, `knowledge-metric-card`, `knowledge-table-card`, `knowledge-table`, `qa-action-bar`, `qa-search-wrap`, `qa-modal-card`, and QA status/type pills with the accepted P0/P1 shell.
- [x] Keep existing add/edit/delete QA modal behavior unchanged.
- [x] Keep "新增 QA", "上传文档", and "问答调试" routes unchanged; do not implement unsupported AI polish or bulk actions.

### Task 2: Documents Page

**Files:**
- Modify: `frontend/src/assets/main.css`
- Modify: `frontend/src/pages/DocumentsPage.vue`

- [x] Refresh `document-page-heading`, `document-upload-panel`, `document-table-header`, `document-toolbar-actions`, `document-status-filter`, `document-name-cell`, and document status pills.
- [x] Add a compact page subtitle that explains supported document ingestion without adding new capabilities.
- [x] Preserve current file input, upload, refresh, delete, filter, and auth redirect logic.

### Task 3: Assistant Debug Page

**Files:**
- Modify: `frontend/src/assets/main.css`
- Modify: `frontend/src/pages/AssistantDebugPage.vue`

- [x] Refresh `assistant-debug-heading`, `assistant-debug-layout`, `debug-chat-panel`, `debug-result-panel`, chat bubbles, input bar, answer cards, missing-field chips, and reference cards.
- [x] Keep the page as a real debug workbench with two panels; do not add unsupported trace tabs, model switches, or vector/LLM internals.
- [x] Preserve current `askAssistant` payload, context handling, clear conversation behavior, and error display.

### Task 4: Settings Page

**Files:**
- Modify: `frontend/src/assets/main.css`
- Modify: `frontend/src/pages/SettingsPage.vue`

- [x] Refresh `settings-page`, `settings-container`, `settings-card`, `profile-section`, `settings-grid`, `system-grid`, and `danger-button`.
- [x] Add safe status-focused copy only; do not expose API key fragments, base URLs, editable secrets, or unsupported notification settings.
- [x] Preserve current logout behavior and `/api/settings/account` data contract.

### Task 5: Verification

**Files:**
- No production file changes expected.

- [x] Run `cd frontend && npm run type-check`.
- [x] Run `cd frontend && npm run lint`.
- [x] Run `cd frontend && npm run build`.
- [x] Browser-check `/knowledge`, `/knowledge/qa`, `/documents`, `/assistant`, and `/settings` in real mode.
- [x] Spot-check mobile width for at least one table page and the assistant debug page.
- [x] Confirm no backend, API, auth, or settings/security boundary was expanded.

---

## Self-Review

- Scope covers P2 visual alignment only.
- No backend API changes.
- No new unsupported features from Stitch are planned.
- Settings remains read-only and status-focused.
