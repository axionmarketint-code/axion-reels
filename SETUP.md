# Setup guide (all free, about 30-40 minutes, easiest on a computer)

What happens once set up: you post in your Telegram channel -> within ~15 minutes a
branded animated video is made and posted to Instagram as a Reel. The same post is also
saved in `x_queue.md` as ready-to-paste X text (X's free API no longer exists).

## Part 1: Telegram bot (5 min)
1. In Telegram, open **@BotFather** -> send `/newbot` -> pick a name and username.
2. Copy the **token** it gives you. Keep it secret.
3. Open your channel **AXIONMarketUpdates** -> Manage channel -> Administrators ->
   add your new bot as an admin (it only needs permission to read posts).

## Part 2: GitHub (10 min)
1. Create a free account at github.com.
2. Create a **new PUBLIC repository** (public is required so Instagram can download the
   videos; your Telegram posts are already public anyway). Name it e.g. `axion-reels`.
3. Upload every file from this folder, keeping the structure, including the hidden
   `.github/workflows/telegram-to-instagram.yml` file.
4. Repo -> Settings -> Secrets and variables -> Actions -> New repository secret:
   - `TELEGRAM_BOT_TOKEN` = the token from Part 1
   - `IG_USER_ID` and `IG_ACCESS_TOKEN` = from Part 3 (add later)
5. Repo -> Settings -> Actions -> General -> Workflow permissions ->
   **Read and write permissions** -> Save.
6. Repo -> Actions tab -> enable workflows -> run **Telegram to Instagram** once by hand.
   The first run only "learns" your current posts and skips them (so old posts don't
   flood Instagram). Every new post after that is processed.

## Part 3: Instagram connection (15-20 min, the fiddly part)
1. Instagram app -> Settings -> Account type -> switch to **Professional** (Creator or Business).
2. Go to developers.facebook.com -> log in -> **Create App** -> type Business.
3. Add the product **Instagram** -> choose "API setup with Instagram login".
4. In that screen, add your Instagram account as a tester / generate a token
   (Meta calls it "Generate access token"). Allow the content publishing permission.
5. Copy the **access token** and your **Instagram user ID** shown on that page.
   Put them in GitHub secrets `IG_ACCESS_TOKEN` and `IG_USER_ID`.
6. Keep the app in **Development mode**. That is fine for posting to your own account
   and needs no app review.

Notes:
- Meta's screens change often; if a label differs, search for "Instagram API with
  Instagram Login content publishing".
- The token lasts about 60 days. Set a reminder to generate a new one and update the secret.
- Instagram allows up to 100 API-published posts per day. Your channel is well below that.
- If GitHub ever pauses the schedule after a long quiet period, press "Enable" on the Actions tab.

## How your channel's posts are handled
- Text posts, and photo posts with a text caption, become Reels. Image-only posts are skipped.
- Long posts (like multi-instrument recaps) are split into up to 4 pages (1/3, 2/3...) so
  text stays large and readable. Extra content ends with "+ more on Telegram".
- Your own disclaimer lines are removed from the video and replaced with one standard
  disclaimer, so it isn't repeated. Green and red dots become up/down triangles
  (emoji can't be drawn in the video font).
- Your header image isn't used in the video. The AXION logo is shown instead.

## Part 4: X (manual, 5 min a day)
Open `x_queue.md` in the repo. Each entry is already under 280 characters with your
Telegram link. Paste your best ones into X's **Schedule** option (free, up to 18 months ahead).

## Your logo
Your transparent AXION Market Intelligence logo is already included as **logo.png** and
appears at the top of every video and on the end card. Since it already shows the full
name, no extra name text is added. To change it later, replace logo.png with a transparent
PNG (at least 900 px wide is ideal). If you switch to a logo without the name in it, set
`LOGO_HAS_NAME: "0"` in the workflow file.

## Templates
- **classic**: navy and teal card, gold accents
- **bold**: black and yellow, big text, no card, high impact
- **terminal**: green-on-black with a typing effect and blinking cursor
`TEMPLATE: auto` rotates through all three so your feed doesn't look repetitive.
To lock one in, change it in the workflow file, e.g. `TEMPLATE: bold`.

## Settings you can change
Edit the `env:` block in `.github/workflows/telegram-to-instagram.yml`:
`BRAND_FULL`, `TEMPLATE`, `TIMEZONE`, `TELEGRAM_LINK`. Optional extras: `HASHTAGS`, `DISCLAIMER`,
`MAX_POSTS_PER_RUN` (default 4).

## Test the video look without any accounts
`python tg2ig.py demo "GOLD +1.2% at 2,650" demo.mp4 all`
(needs Python, Pillow and ffmpeg). Green/red colouring is automatic for numbers
starting with + / - and for BUY / SELL words.

## Always include
The videos and captions carry a "not financial advice" disclaimer. Keep it.
