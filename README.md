# the landline

A single page awareness site for The Landline, a listening movement incubated by Mini Miles.

Phase 1 only. Awareness and belief, not transactions. The page is a short scroll story: it opens in the dark with a phone that makes one call, walks the reader through why the earliest years of a life matter and what most of us quietly carry from them, then resolves into warm light with one invitation: pick up.

## Running it

It is a single self contained file. Fonts are embedded, so the type renders correctly online or off. Open `index.html` in a browser, or serve the folder:

```
python3 -m http.server 8000
```

Then visit `http://localhost:8000`.

## Two things to wire before launch

1. **Form endpoint.** The signup form has full UI and validation but no live backend. Search `index.html` for `STUB ENDPOINT` and replace the simulated success block with a real `fetch` to your provider of choice. Keep the optional message field private: store it, never display it.

2. **OG image.** The page references `og-image.jpg`. Add the black phone on black, receiver off the hook, with one warm glow, at 1200 by 630.

## Notes

- Type is Fraunces for the voice and Inter for the body, both embedded as base64 woff2, so nothing depends on a font CDN.
- The journey goes from dark to light. The hero is the only dark scene; the story is set on warm paper for readability, and the call to action is the brightest, warmest point.
- Big statements animate in line by line on scroll. Content is visible by default and only opts into animation when JavaScript and motion are allowed.
- The dial tone hum is off by default and only starts on a tap, respecting autoplay policies.
- Motion respects `prefers-reduced-motion`. Mobile first, no horizontal scroll.
- No em dashes anywhere, by design.

Built for Sachin, Mini Miles.
