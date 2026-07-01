# Stitch UI Refresh Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Apply the approved Stitch-inspired visual refresh to the current customer service bot without expanding backend scope or changing real API behavior.

**Architecture:** Keep all existing Vue services, routes, data contracts, and backend APIs intact. Refresh the shell, shared visual language, and core workflow pages through Vue template/CSS changes only, with P0 global baseline and P1 core workflow pages first.

**Tech Stack:** Vue 3, Vite, TypeScript, CSS, existing Material Symbols icons, existing REST services.

---

### Task 1: Global Visual Baseline

**Files:**
- Modify: `frontend/src/assets/main.css`
- Modify: `frontend/src/components/AppLayout.vue`

- [x] Introduce Stitch-inspired design tokens: slate background, primary blue, AI cyan, semantic status colors, 8px radius, compact table spacing.
- [x] Update app shell, sidebar, top bar, buttons, cards, tags, table, feedback, and modal base styles.
- [x] Keep current navigation items and auth/logout behavior unchanged.
- [x] Verify `cd frontend && npm run type-check` passes.

### Task 2: Core Workflow Pages

**Files:**
- Modify: `frontend/src/pages/DashboardPage.vue`
- Modify: `frontend/src/pages/TicketPoolPage.vue`
- Modify: `frontend/src/pages/MyTicketsPage.vue`
- Modify: `frontend/src/pages/TicketDetailPage.vue`
- Modify: `frontend/src/assets/main.css`

- [x] Refresh dashboard metrics, ticket table, quick actions, and right AI assistant panel using current dashboard APIs.
- [x] Refresh ticket pool and my tickets tables with compact filters, status tags, and action links.
- [x] Refresh ticket detail into a clearer three-column workbench: ticket info, conversation/reply, AI suggestions/references.
- [x] Keep all existing service calls, field names, and auth redirects unchanged.
- [x] Ensure no `[Mock]` badge appears in real mode.

### Task 3: Verification

**Files:**
- No production file changes expected.

- [x] Run `cd frontend && npm run type-check`.
- [x] Run `cd frontend && npm run lint`.
- [x] Run `cd frontend && npm run build`.
- [x] Browser-check `http://127.0.0.1:5199/` in real mode for login, dashboard, ticket pool, ticket detail.
- [x] Confirm settings/security boundaries were not expanded.

---

## Self-Review

- Scope covers approved P0/P1 only.
- No backend API changes.
- No new unsupported features from Stitch.
- Plan intentionally does not implement P2 pages yet; they follow after P0/P1 is accepted.
