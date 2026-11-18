# AXION Market Intelligence: growth plan and automation notes
Last updated: 2026-11-18

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
- [ ] Step 2: add the bot as admin of the channel (instructions given, awaiting confirmation)
- [ ] Step 3: create free GitHub account + PUBLIC repo, upload files, set Actions
      permission to Read and write
- [ ] Step 4: add secret TELEGRAM_BOT_TOKEN
- [ ] Step 5: create Instagram account, switch to Professional, create Meta developer app,
      get IG_USER_ID and IG_ACCESS_TOKEN (token expires about every 60 days)
- [ ] Step 6: run the workflow by hand once (first run skips old posts)

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
Practical:
- Version history, easy edits via one file, backups, more automations in the same account

## Cautions
- Never share or paste the bot token or Instagram token in chats or public files.
- Meta's developer screens change often; labels may differ from SETUP.md.
- Platforms like YouTube and TikTok need their own account approvals.
