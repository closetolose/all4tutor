# Phase 1 – Audit results

**Scope:** Quick pass at 375px for horizontal scroll, missing padding, touch targets < 44px, input font-size < 16px. Add lesson template resolved.

## Add lesson

`core/add_lesson.html` was missing (view used it; only `mobile/add_lesson.html` existed). Created minimal `core/add_lesson.html` that extends `core/base.html`, uses a single card and the same form fields, with layout and classes aligned to Batch 1 (form-label, form-group, btn, 4px grid).

## Findings by screen group

- **Base / Auth (Login, Register, Auth base):** Main content had no max-width container on desktop; mobile used `padding: 12px` on `.main-content` (auth used 20px on `.auth-flex-container`) — risk of content touching edges at 375px. Buttons and auth inputs were not explicitly set to min-height 48px on mobile; generic inputs used font-size 14px (can trigger iOS zoom below 16px). Cookie banner on register had horizontal padding but no safe zone when viewport is narrow.

- **Desktop shell (base.html):** Sidebar + main; main had padding 32px 40px but no inner wrapper with max-width 1200px. On 768px media query, main padding was 12px — below 16px safe zone.

- **Mobile shell (mobile/base.html):** Content area uses sections with margin 0 15px; no global 16px safe zone on the main content wrapper. Header and drawer already use adequate touch targets (44px) in places.

- **Index, lists, cards (My students, Tutor card, etc.):** Not audited in detail for Phase 1; Batch 1 limits changes to Base and Auth only.

## Summary

Batch 1 targets Base, Auth base, Login, Register: add main content container (max-width 1200px), safe zones (padding 0 16px at max-width 768px), buttons min-height 48px on mobile, input/textarea/select font-size ≥ 16px, and CSS variables for component colors so these screens pass the four Verifier criteria at 375px.
