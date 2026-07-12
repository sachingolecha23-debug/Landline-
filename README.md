# The Landline

A single page awareness site for The Landline, a listening movement incubated by Mini Miles.

Phase 1 only. Awareness and belief, not transactions. The visitor scrolls down through darkness, the tunnel, and the page gradually introduces warm light as they descend, ending in the brightest section: the call to action.

## Running it

It is a single self contained file. Open `index.html` in a browser, or serve the folder:

```
python3 -m http.server 8000
```

Then visit `http://localhost:8000`.

## Two things to wire before launch

1. **Form endpoint.** The signup form has full UI and validation but no live backend. Search `index.html` for `STUB ENDPOINT` and replace the simulated success block with a real `fetch` to your provider of choice. Keep the optional message field private: store it, never display it.

2. **OG image.** The page references `og-image.jpg`. Add the black phone on black, receiver off the hook, with one warm glow, at 1200 by 630.

## Notes

- Fonts load from Google Fonts. If you self host later, swap the `<link>` in the head.
- The dial tone hum is off by default and only starts on a tap, respecting autoplay policies.
- Motion respects `prefers-reduced-motion`.
- No em dashes anywhere, by design.

Built for Sachin, Mini Miles.
