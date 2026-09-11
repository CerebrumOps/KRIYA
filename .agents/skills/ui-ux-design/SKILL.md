---
name: ui-ux-design
description: Master skill for Web UI/UX design, modern React 19, TypeScript, Tailwind CSS, responsive industrial dashboards, generative UI widgets, and streaming AI interaction patterns. Use when designing, building, or refining frontend interfaces, animations, and user experiences.
---

# UI/UX & Web Design Mastery Skill

This skill guides the design and implementation of modern, responsive, high-performance web user interfaces for AI workbenches and industrial applications.

---

## 1. Visual & Design System Principles

### A. Dark-Theme Industrial Aesthetic
- **Backgrounds**: Deep neutral slate tones (`#0b0d13`, `#12151f`, `#1a1e2e`) rather than pure black (`#000000`) for depth.
- **Card Surfaces**: Semi-transparent card layers (`rgba(26, 30, 46, 0.7)`) with subtle borders (`rgba(255, 255, 255, 0.08)`) and backdrop blur (`backdrop-blur-md`).
- **Accents**: 
  - Primary Action / AI Glow: Vibrant Violet/Indigo (`#8b5cf6` / `#6366f1`).
  - Success / Online: Emerald Green (`#10b981`).
  - Warning / Caution: Amber (`#f59e0b`).
  - Critical / Error: Rose/Crimson (`#ef4444`).

### B. Typography & Layout
- **Font Stack**: Modern geometric sans-serif (`Inter`, `Plus Jakarta Sans`, system sans) for UI, and clean monospace (`JetBrains Mono`, `Fira Code`, monospace) for code and sensor telemetry.
- **Spacing Scale**: Consistent 4px/8px grid system (`gap-2`, `gap-3`, `gap-4`, `p-4`, `p-6`).
- **Readability**: Maximum line length of 70–80 characters for text paragraphs, line height `leading-relaxed` (1.625).

---

## 2. Real-Time AI Streaming UX

### A. Streaming Thought & Reasoning (`<think>`)
- Wrap reasoning chains into a collapsible thought card above the main response.
- Show a pulsing amber/violet dot while reasoning tokens arrive.
- Auto-collapse thoughts once the final content begins streaming so the user immediately sees the answer, but allow one-click expansion to inspect the thought process.

### B. Live Token Cursor
- When streaming is active, render an animated vertical pulse cursor (`inline-block w-1.5 h-4 bg-violet-400 animate-pulse ml-0.5 align-middle`).
- Remove the cursor cleanly as soon as streaming completes.

### C. Performance & Metrics Badges
- Render generation telemetry unobtrusively in the message footer:
  - Model name badge (e.g. `Qwen 2.5 7B`)
  - Speed badge (e.g. `43.8 tok/s`)
  - Duration badge (e.g. `1.85s`)
  - Token count badge (e.g. `240 tokens`)
- Include a quick copy button that provides immediate visual feedback (`Copied!` with checkmark for 2 seconds).

---

## 3. Tool Execution Drawer & Side Panels

- **Right Rail Tool Panel**:
  - Keep collapsed by default to maximize chat reading space.
  - Automatically slide open or pulse a status dot when an active tool begins executing (`running` status).
  - Each tool card should show: Tool Name, Index (`#1`), Status badge (`Running` / `Completed` / `Failed`), Execution time in milliseconds, and collapsible JSON Arguments & Results with one-click copy.

---

## 4. Generative UI Inline Embeds

When rendering custom interactive widgets inline:
```html
<script src="https://www.gstatic.com/antigravity/web/dev/tailwindcss.min.js"></script>
<body class="bg-transparent text-[var(--foreground)] antialiased p-4">
  <div class="bg-[var(--card)] border border-[var(--border)] rounded-xl p-5 shadow-sm">
    <!-- Interactive component -->
  </div>
</body>
```
- Never use viewport-relative heights (`h-screen`, `100vh`) inside inline iframe widgets.
- Keep inline widgets compact (under 500px tall).
