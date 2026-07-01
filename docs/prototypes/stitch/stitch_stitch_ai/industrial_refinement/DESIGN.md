---
name: Industrial Refinement
colors:
  surface: '#faf8ff'
  surface-dim: '#d9d9e5'
  surface-bright: '#faf8ff'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f3f3fe'
  surface-container: '#ededf9'
  surface-container-high: '#e7e7f3'
  surface-container-highest: '#e1e2ed'
  on-surface: '#191b23'
  on-surface-variant: '#434655'
  inverse-surface: '#2e3039'
  inverse-on-surface: '#f0f0fb'
  outline: '#737686'
  outline-variant: '#c3c6d7'
  surface-tint: '#0053db'
  primary: '#004ac6'
  on-primary: '#ffffff'
  primary-container: '#2563eb'
  on-primary-container: '#eeefff'
  inverse-primary: '#b4c5ff'
  secondary: '#006b5f'
  on-secondary: '#ffffff'
  secondary-container: '#6df5e1'
  on-secondary-container: '#006f64'
  tertiary: '#943700'
  on-tertiary: '#ffffff'
  tertiary-container: '#bc4800'
  on-tertiary-container: '#ffede6'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#dbe1ff'
  primary-fixed-dim: '#b4c5ff'
  on-primary-fixed: '#00174b'
  on-primary-fixed-variant: '#003ea8'
  secondary-fixed: '#71f8e4'
  secondary-fixed-dim: '#4fdbc8'
  on-secondary-fixed: '#00201c'
  on-secondary-fixed-variant: '#005048'
  tertiary-fixed: '#ffdbcd'
  tertiary-fixed-dim: '#ffb596'
  on-tertiary-fixed: '#360f00'
  on-tertiary-fixed-variant: '#7d2d00'
  background: '#faf8ff'
  on-background: '#191b23'
  surface-variant: '#e1e2ed'
typography:
  display-lg:
    fontFamily: Outfit
    fontSize: 32px
    fontWeight: '600'
    lineHeight: 40px
    letterSpacing: -0.02em
  headline-md:
    fontFamily: Outfit
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
    letterSpacing: -0.01em
  headline-sm:
    fontFamily: Outfit
    fontSize: 20px
    fontWeight: '500'
    lineHeight: 28px
    letterSpacing: '0'
  body-lg:
    fontFamily: Geist
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
    letterSpacing: '0'
  body-md:
    fontFamily: Geist
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
    letterSpacing: '0'
  body-sm:
    fontFamily: Geist
    fontSize: 12px
    fontWeight: '400'
    lineHeight: 18px
    letterSpacing: '0'
  label-md:
    fontFamily: Geist
    fontSize: 13px
    fontWeight: '500'
    lineHeight: 16px
    letterSpacing: 0.02em
  mono-sm:
    fontFamily: Geist
    fontSize: 12px
    fontWeight: '400'
    lineHeight: 16px
    letterSpacing: '0'
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  unit: 4px
  container-padding: 24px
  gutter: 16px
  stack-sm: 8px
  stack-md: 16px
  stack-lg: 24px
  inset-squish-sm: 4px 8px
  inset-squish-md: 8px 16px
---

## Brand & Style

The design system is engineered for high-stakes SaaS operations where information density and clarity are paramount. The brand personality is **Clinical, Systematic, and Efficient**, catering to power users who require a high-performance environment for complex data management.

The visual style follows a **Corporate / Modern** aesthetic with a lean towards **Minimalism**. Every interface element is strictly functional; decorative flourishes are removed in favor of clear visual hierarchies and robust structural alignment. The user should feel a sense of absolute control and reliability, as if operating a precision instrument.

**Core Principles:**
- **Density over Air:** Maximize the visibility of data without sacrificing legibility.
- **Functional Color:** Color is used exclusively for state communication and primary actions.
- **Structural Integrity:** Elements are aligned to a rigid grid to reinforce a sense of order.

## Colors

This color palette is designed for prolonged professional use, prioritizing low eye strain and high semantic clarity.

- **Canvas & Surface:** The `#F7F8FA` canvas provides a cool, clinical backdrop, while `#FFFFFF` surfaces are used for interactive containers and cards to create a clear "layer" of work.
- **Primary & Secondary:** `#2563EB` (Blue) serves as the primary driver for navigation and core system actions. `#14B8A6` (Teal) is utilized for secondary data visualizations or supportive highlights.
- **Feedback Loop:** Success, Danger, and CTA (Warning/Attention) colors are strictly reserved for status indicators, validation messages, and high-priority interrupts.
- **Neutral Stack:** Text hierarchy is established through `#18181B` for readability and `#71717A` for metadata and non-essential labeling.

## Typography

The typography system utilizes **Outfit** for structural headings to provide a modern, geometric clarity, and **Geist** for body text and UI labels to leverage its technical, developer-centric legibility.

**Implementation for Chinese Text:**
- For all Chinese characters, fall back to `PingFang SC`, `Hiragino Sans GB`, or `Microsoft YaHei` in that order.
- Ensure line-heights are strictly maintained to prevent character clipping in dense data tables.
- Standard body text size is set to `14px` (body-md) to maximize information density while remaining accessible.
- Labels (label-md) should be used for form headers and table columns, often paired with slightly increased letter spacing for rapid scanning.

## Layout & Spacing

The layout is optimized for a **desktop-first fluid grid**. It uses an 8px base grid with a 4px sub-grid for fine-grained component internal spacing.

- **Grid:** 12-column system with 16px gutters for main content areas.
- **Margins:** Standard page margin is 24px, increasing to 32px on ultra-wide displays.
- **Density:** In data-heavy views (Tables, Dashboards), use "Compact" spacing (4px gutters) to minimize scrolling.
- **Sidebars:** Fixed-width navigation (240px) or collapsible icon-only state (64px).
- **Responsive Reflow:** On tablet, transition to a 1-column layout for side-panels; on mobile (secondary priority), utilize full-screen modal overlays for complex operations.

## Elevation & Depth

This design system avoids heavy shadows, favoring **Tonal Layers** and **Low-Contrast Outlines** to define hierarchy.

- **Level 0 (Canvas):** `#F7F8FA` - The base background.
- **Level 1 (Surface):** `#FFFFFF` with a 1px border of `#E4E4E7`. Used for cards, tables, and main content blocks.
- **Level 2 (Overlays):** For dropdowns and menus, use `#FFFFFF` with a very soft, subtle shadow: `0px 4px 6px -1px rgba(0, 0, 0, 0.1)`.
- **Level 3 (Modals):** Max 12px corner radius. Requires a `#18181B` backdrop at 40% opacity to isolate the task.
- **Interactive States:** Use subtle background shifts (e.g., `#F4F4F5` on hover) instead of elevation changes.

## Shapes

The geometry of the design system is strictly controlled to maintain an industrial feel.

- **Standard Components:** Buttons, Input fields, and Chips must use exactly **8px (0.5rem)** corner radius.
- **Large Containers:** Cards and Sections also use **8px**.
- **Dialogs & Modals:** For larger floating surfaces, the radius is increased to **12px (0.75rem)** to provide a slightly softer distinction from the background grid.
- **Strict Rule:** No fully rounded (pill) shapes are allowed, except for status dots or notification badges.

## Components

**Buttons**
- **Primary:** Background `#2563EB`, Text `#FFFFFF`. Solid fill, no gradient.
- **Secondary:** Background `#FFFFFF`, Border `#E4E4E7`, Text `#18181B`.
- **CTA:** Background `#F59E0B`, Text `#18181B`. Reserved for "Action Required" states.

**Input Fields**
- Height: 36px (Standard), 32px (Compact).
- Border: 1px `#E4E4E7`.
- Focus State: 1px `#2563EB` border with a 2px blue outer glow at 10% opacity.
- Placeholder text in Chinese: `请输入...` or `搜索...`.

**Data Tables (Crucial Component)**
- Row Height: 40px for high density.
- Header: Background `#F7F8FA`, Text `#71717A` (label-md).
- Border: 1px horizontal lines only (`#E4E4E7`). No vertical lines between columns.

**Chips / Tags**
- Flat background (e.g., `#E4E4E7` for neutral, `#DCFCE7` for success).
- No border. 8px corner radius.

**Lists**
- Use `#F7F8FA` hover states for list items to indicate interactivity without visual clutter.