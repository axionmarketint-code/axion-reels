# AXION Market Intelligence: growth plan and automation notes
Last updated: 2026-11-18 (afternoon)

## Goal
Grow subscribers of the Telegram channel **AXION | MARKET INTELLIGENCE**
(t.me/AXIONMarketUpdates, about 3 subscribers on 2026-11-17) at **zero cost**,
by automating its market updates to X and Instagram.

## Facts about the setup
- Updates are posted into the channel by the user's existing **MT5 bot** (do not touch it).
- Post types seen: NY Close Recap, Setup Developing, End-of-Day Summary, forex/crypto
  signals (entry, SL, TP1/TP2, analysis), US Session Check, News Result. Most are text
  with a header image; some are image-only.
- User has an X account. Instagram account is not created yet (must be switched to
  Professional/Creator later).
- Logo: gold eagle, "AXION MARKET INTELLIGENCE", transparent version saved as logo.png.

## Key decisions
- **X:** X's free API ended (Feb 2026; posting is pay-per-call), so X is NOT automated.
  Each post is saved to x_queue.md (under 280 chars, with the Telegram link) for the
  user to paste into X's free Schedule feature (~5 min/day).
- **Instagram:** fully automated and free. Telegram bot reads the channel, Python +
  Pillow + FFmpeg builds a 9:16 Reel, GitHub Actions runs it about every 15 min,
  Instagram Graph API publishes it.
- A **second, separate Telegram bot** is used for the pipeline (not the MT5 bot).
- "Interactive" video is not possible on Instagram. Closest free options: comment-trigger
  CTAs, poll stickers on Stories (manual), link in bio.
- Every video and caption carries a "not financial advice" disclaimer. Keep it.
- Templates: classic (navy/gold), bold (black/yellow), terminal (green typing effect).
  The white "light" template was removed at the user's request. TEMPLATE=auto rotates.
- Long posts are split into up to 4 pages; the channel's own disclaimer lines are
  stripped and replaced by one standard disclaimer; image-only posts are skipped.

## Setup progress
- [x] Project built and tested (tg2ig.py, workflow, SETUP.md, axion-reels.zip)
- [x] Logo added, background removed
- [x] Step 1: new Telegram bot created via @BotFather (user confirmed). Token kept private.
- [x] Step 2: bot added as admin of the channel (user confirmed)
- [x] Step 3: GitHub account + public repo created, files uploaded; workflow fixed
      (folder must be named .github with a leading dot)
- [x] Step 4: TELEGRAM_BOT_TOKEN secret added; first workflow run succeeded (green check)
- [ ] Real test: post a test line in the channel, re-run workflow, check x_queue.md
- [x] Meta developer app created: "AXION News Reels" (Business type, Development mode),
      Instagram product added. Meta now labels the route "API setup with Unified login".
- [ ] BLOCKED/WAITING (2026-11-19): Meta asks to create a business portfolio (free; name
      "AXION Market Intelligence"). User's Facebook account is too new, will retry in ~1 hour.
      Do NOT start Business Verification unless Meta blocks publishing.
- [ ] 2026-11-20: Unified login page shows Step 1 "Configure your app" -> "Create new configuration"
      (system-user token, never expires; permissions incl. instagram_basic and
      instagram_content_publish). This is the Facebook-login style, so the workflow needs
      IG_GRAPH_HOST: https://graph.facebook.com (added). Untested against Instagram.
- [ ] Then: Unified login -> Add account -> Generate token -> copy IG token + account ID
- [ ] Step 5: create Instagram account, switch to Professional, create Meta developer app,
      get IG_USER_ID and IG_ACCESS_TOKEN (token expires about every 60 days)
- [ ] Step 6: run the workflow by hand once (first run skips old posts)

## MILESTONE (2026-11-20)
First Reel published to Instagram automatically from the Telegram channel; user confirmed it
is live. Pipeline works end to end: Telegram -> GitHub Actions -> video with sound -> Instagram.
Instagram notice: professional account restricted from ADVERTISING only (ads, boosts, pixel);
organic posting unaffected. User chose to skip the review for now.
Remaining: watch first real posts, tune templates/sound/captions, keep X manual, growth tactics.

## Filter (2026-11-20)
User does NOT want trade setups/signals sent. Added skip_reason() filter (title/keyword lists,
optional ONLY_TITLE_WORDS). Needs updated tg2ig.py on GitHub. Defaults are guesses based on
post types seen (Setup Developing, signals with Entry/SL/TP); user to confirm real labels.

## Network retry (2026-11-20)
A run failed with RuntimeError "Network error (ConnectionError)" (transient). http() now
retries 4 times (5s/15s/30s waits). Failed runs lose nothing: Telegram offset is only saved
at the end of a successful build. Needs the updated tg2ig.py on GitHub.

## Channel plan and Instagram fallback (2026-11-21)
Channels: (1) Market updates = public, promoted, the only one the pipeline bot reads.
(2) Setups + weekly report (Friday 5pm Toronto time, use Telegram's native Schedule message);
bot is NOT admin there so setups never leak. (3) Feedback channel with a separate bot and
approve-before-post flow: to build later.
Instagram API stopped working for the user ("blocked"; exact error not yet seen). Chose
fallback: pipeline sends Reel + IG caption + X text to a private Telegram chat; user posts
by hand (or Meta Business Suite). Implemented as DELIVERY=telegram, REVIEW_CHAT_ID secret.
Do NOT use unofficial Instagram tools or browser bots (ban risk, against rules).

## X decision (2026-11-18)
User obtained X API access, but it is pay-per-use: $0.015 per plain post, $0.20 per post
with a URL; no free tier (one-time $20 credit after a first credit purchase). User chose
to STAY MANUAL AND FREE. RSS-to-X tools were checked: free caps are tiny (dlvr.it free =
10 posts/month per its help page), so not useful. Revisit option: automate X with
text-only posts (about $3-4/month, no links, Telegram link in bio) with a spending cap.

## Sound (2026-11-20)
Reels now include audio: an original generated music bed per template (numpy, royalty-free),
or the user's own tracks from a music/ folder in the repo. Needs numpy in requirements.txt
and updated tg2ig.py uploaded to GitHub. AUDIO=off disables. Instagram's music library
is not available to API posts. Sound quality was only checked by levels, not by ear.

Audio styles built 2026-11-20: news, cinematic, corporate, lofi (AUDIO_STYLE env, comma list
rotates). User chose NEWS and LOFI (AUDIO_STYLE: "news,lofi").

## Why GitHub
Free always-on runner (Actions), public hosting for the videos so Instagram can download
them, safe storage for tokens (Secrets), saved X queue, version history and backups.

## Future development ideas (to bring back later)
Content:
- Daily recap Reel combining the day's updates at market close
- Auto-generated charts and price cards from free market data
- Economic calendar posts ("Tomorrow's key events")
- Instagram carousels from recaps
- Story versions of signals and news results
- Big single-asset price card template for alerts
Growth:
- Reuse the same vertical videos on YouTube Shorts and TikTok
- Weekly performance summary post (present honestly)
- Daily subscriber-count logging to see which content brings people in
- Free tactics: link in bio, one public teaser per day, reply to large market accounts on
  X with useful data, consistent hashtags, post at market open and close
- Keep the generated videos (instead of deleting after Instagram publish) so they can be
  uploaded by hand to X's free scheduler (user said: not yet)
Practical:
- Version history, easy edits via one file, backups, more automations in the same account

## Cautions
- Never share or paste the bot token or Instagram token in chats or public files.
- Meta's developer screens change often; labels may differ from SETUP.md.
- Platforms like YouTube and TikTok need their own account approvals.

## Market Alert generator (2026-11-22)
Built from the user's reference video (1080x1920, 15s, no audio). Files: alert_template.py (Pillow+ffmpeg renderer + parse_alert),
generator/index.html (web app: paste-to-fill, live preview, in-browser MP4 export via WebCodecs + own muxer; tested in headless Chromium
and ffprobe), desktop_app.py (Tkinter; NOT tested, no display here), fonts/ (DejaVu).
GitHub: .github/workflows/web-app.yml publishes generator/ on GitHub Pages (Settings > Pages > Source: GitHub Actions);
desktop-app.yml builds Windows/Mac/Linux apps via PyInstaller (run by hand, download from run Artifacts; untested).
Pipeline: tg2ig.py auto-uses the template for posts with pips + from/to price + sharp/spike/alert wording (ALERT_TEMPLATE=off disables).
Parser tuned only on invented text: need 2-3 real "sharp move" posts. Pixel diff vs reference: edges only (fonts/antialiasing).
