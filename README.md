# twg-assets

Assets for the "Things You Wouldn't Google" TikTok slideshows.

- `backgrounds/` — AI-generated background photos (FLUX Schnell, 768x1344, 9:16), named `<theme>_<nnn>.jpg`. Upscaled to 1080x1920 at render time.
- `backgrounds.csv` — manifest of every background with its theme and the date it was last used (empty = never).
- `posts/` — rendered slides for each published post (public URLs are handed to Metricool).

Public raw URL pattern: `https://raw.githubusercontent.com/JaredLederman1/twg-assets/main/<path>`
