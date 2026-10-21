# Daily run: Things You Wouldn't Google

Goal: publish 10 photo slideshows per day to TikTok @thingsyouwouldntgoogle via Metricool,
90 minutes apart from 9:00 AM to 10:30 PM America/New_York.

## Fixed facts
- Repo: JaredLederman1/twg-assets (public). Raw URL base: https://raw.githubusercontent.com/JaredLederman1/twg-assets/main/
- Metricool brand: "Things You Wouldn't Google", blogId 7553660, timezone America/New_York, network tiktok.
- Post times (ET): 09:00, 10:30, 12:00, 13:30, 15:00, 16:30, 18:00, 19:30, 21:00, 22:30.
- Each slideshow = 7 slides: title, 5 questions (q/a), end. Background per slide from `backgrounds/`.

## Steps
1. Setup
   - Attach the repo with push access (add_repo owner=JaredLederman1 repo=twg-assets access=push), clone it to /home/claude/twg-assets.
   - Ensure tooling: `python3 -c "import playwright"` else `pip install --break-system-packages playwright && python3 -m playwright install chromium`.
     Ensure fonts: `fc-list | grep -i "Inter"` and `fc-list | grep -i "Noto Color Emoji"`; if missing, download Inter (github.com/rsms/inter releases, Inter-4.1.zip, extras/otf/Inter-*.otf) and NotoColorEmoji.ttf (github.com/googlefonts/noto-emoji/raw/main/fonts/NotoColorEmoji.ttf) into ~/.local/share/fonts and run `fc-cache -f`.
2. Write content
   - Read `posts/questions_log.csv` (columns: date,post,question). Never reuse a question already in it (or a near-duplicate).
   - Write 10 slideshows. Each: a title-slide hook + kicker, 5 questions, a closing slide.
     - Topics people are embarrassed or scared to Google: body, health quirks, sex and relationships (non-explicit), breakups, dating, friendships, family, money, work, sleep, mental health, hygiene, aging. Mix topics within a slideshow or theme a slideshow ("5 breakup questions you'd never ask out loud").
     - Hooks rotate, e.g. "5 things you'd never Google 🫣", "Questions you're too scared to Google", "Things I'd only ask at 2am", "Things your doctor wishes you'd just ask", "Breakup questions you'd never say out loud". Kicker examples: "be honest…", "no judgement", "asking for a friend". Closing title like "Which one did you secretly need? 👀" with sub "comment the number. no one's judging" (vary wording).
     - Question: short, first-person, how a real person would type it. Answer: a warm short paragraph of 45–60 words, written like a kind older sibling: one or two concrete facts, reassurance, and a "worth seeing a doctor if…" line when medically relevant.
   - Fact-check every answer yourself before rendering. Drop and replace anything uncertain, contested, dangerous, sexually explicit, or that gives dosing/medical instructions. Nothing involving minors, self-harm, eating disorders, drugs or weapons.
3. Render
   - `python3 pipeline/pick_backgrounds.py 70 YYYY-MM-DD` → 70 background paths (assign 7 per slideshow in order).
   - For each slideshow k=01..10 write posts/YYYY-MM-DD/k/spec.json and run `python3 pipeline/render.py posts/YYYY-MM-DD/k/spec.json posts/YYYY-MM-DD/k`. It must exit 0 (no overlaps/overflow). If not, shorten the offending text and re-render.
   - Visually spot-check at least slides 1, 2 and 7 of two slideshows (Read the JPGs).
4. Publish assets
   - Append the 50 questions to posts/questions_log.csv. Commit everything (backgrounds.csv, posts/) and push to main. Before pushing: `git fetch origin main && git rebase FETCH_HEAD`, then `git push origin HEAD:main`.
   - Verify each slide's raw URL returns HTTP 200 with curl before scheduling (raw.githubusercontent can take a minute to update; retry).
5. Schedule in Metricool (createScheduledPost, one call per slideshow)
   - blogId 7553660, date/publicationDate at that slot in America/New_York, providers [{"network":"tiktok"}], autoPublish true, media = the 7 raw URLs in slide order.
   - text: a short lowercase caption with a question to drive comments, plus 3–5 hashtags including #thingsyouwouldntgoogle (e.g. "the questions we've all typed and deleted 🫣 which one was you? #thingsyouwouldntgoogle #relatable #fyp").
   - tiktokData: {"privacyOption":"PUBLIC_TO_EVERYONE","disableComment":false,"disableDuet":false,"disableStitch":false,"commercialContentThirdParty":false,"commercialContentOwnBrand":false,"title":<the title-slide hook>,"autoAddMusic":true,"photoCoverIndex":0,"isAigc":false}
   - Skip any slot already in the past. If Metricool returns an error (e.g. plan post limit), stop and report it.
6. Report: one short summary (posts scheduled with times + hooks, anything skipped, any errors).

## Background pool
The pool in `backgrounds/` is final. Never generate new background images; always reuse them via `pipeline/pick_backgrounds.py` (least recently used first).
