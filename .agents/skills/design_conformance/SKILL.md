---
name: design_conformance
description: Audit workspace React JSX and CSS files for conformance with the project's design tokens and layout rules defined in design.md.
---

# Skill: Design System Conformance Audit

## Purpose

Enforce styling consistency, grid scale alignment, shape standards, and color themes across the frontend codebase based on design system rules.

## Core Rules

1. **Token Retrieval**: Check `design.md` at the project root for color, typography, shape (corner radius), and spacing tokens.
2. **CSS Analysis**: Ensure all CSS declarations use CSS variable tokens (e.g. `var(--spacing-md)`, `var(--rounded-md)`, `var(--text-primary)`) rather than hardcoded hex colors, pixels, or inline styling.
3. **React/JSX Inspection**: Do not allow inline style objects (e.g., `style={{ gap: '8px' }}`) inside JSX templates. All layout and style behaviors must reside in stylesheet files.
4. **Contrast Compliance**: Check that text colors and background pairs satisfy accessibility contrast.
5. **Linting Report**: Output a report summarizing drifts, affected files, line numbers, and proposed diff-based corrections.

Refer to the format and validation specifications in [spec.md](file:///.agents/skills/design_conformance/references/spec.md) for more details.
