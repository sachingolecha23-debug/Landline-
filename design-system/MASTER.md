# The Landline, Design System (Master)

Audited and structured with the UI UX Pro Max design-intelligence skill.
Pattern: Scroll-Triggered Storytelling. One idea per screen, a progress indicator, mini CTA at the turn, final climax CTA. The journey runs dark to light: the tunnel, the years rolling back, the light of childhood.

## Palette

| Token | Value | Use |
|---|---|---|
| --ink | #101010 | The dark act: hero, who, years. Never pure black |
| --paper | #F3EEE4 | The light act: story, questions, movement |
| --paper-warm | #F7EAD6 | The warmest zones: turn, CTA, finale |
| --text | #1A1714 | Headlines on paper |
| --text-soft | #554C42 | Body on paper, 4.5:1+ |
| --text-faint | #7C7263 | Hints and placeholders, kept above 4.5:1 |
| --onink | #F1ECE3 | Headlines on ink |
| --onink-soft | #A7A097 | Body on ink |
| --amber | rgb(214, 150, 74) | The one warm light. Glows, the cord, accents |
| --amber-lo | rgb(232, 196, 140) | Lighter warm, tips and highlights |

Rule: amber is light, not paint. It appears as glow, halo, wire and punctuation, never as large filled UI surfaces.

## Type

| Role | Face | Notes |
|---|---|---|
| Voice / display | Fraunces (560 to 640) | Embedded woff2, no CDN. Italic for the emotional register |
| Body | Inter (embedded as InterEmbed) | 400, generous line height 1.7 |
| Operator / labels | ui-monospace stack | Uppercase, letterspaced .3em+, tiny |

Scale contrast between hero and body is at least 5:1.

## Motion

- Scroll is the timeline. Pinned scrub scenes (years odometer, questions) ease toward scroll targets with a lerp ticker, never raw-wheel.
- Reveals: opacity and transform only. Slow, heavy easing: cubic-bezier(.22, .61, .36, 1).
- The 3D hero (Three.js, embedded) idles, follows the pointer, rings near the CTA, dips away on scroll.
- Every scene has exactly one or two animated focal elements, never more.
- prefers-reduced-motion: scrub scenes lay out statically, GL never mounts, reveals render visible.

## Non negotiables (from the brief)

- No em dashes anywhere.
- No fearmongering, no countdowns, no lecturing parents, no fake numbers.
- The phone number does not exist yet: "The line opens soon."
- Mini Miles appears only as the quiet footer credit.

## Checklist status (UI UX Pro Max pre-delivery)

- [x] No emojis as icons
- [x] cursor-pointer on clickable elements
- [x] Hover states with smooth transitions
- [x] Paper text contrast 4.5:1 minimum
- [x] Focus states visible for keyboard nav (warm focus-visible ring)
- [x] prefers-reduced-motion respected
- [x] Responsive at 375, 768, 1024, 1440
- [x] Required form fields marked, labels bound, submit feedback shown
- [x] Progress indicator (warm hairline)
- [x] Mobile: heavy animation simplified (no WebGL, static fallbacks)
