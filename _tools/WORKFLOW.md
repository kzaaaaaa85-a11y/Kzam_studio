# Daily post + reel for kzamstudio.com

One SEO article and one reel per day for the Kzam Studio blog. The owner (Ismail) is shown every
draft before it goes live.

Since 7 Oct 2026 publishing is automatic, at his request ("عايز نشر أوتوماتيك بس تعرض عليّ قبل
النشر"): the morning run makes the draft and sends it to him, and the evening run (about 20:00
Europe/Paris, a separate scheduled task) publishes it on the site, Instagram, LinkedIn and X
without waiting for a reply. He stops or changes a draft by replying before the evening run.
Nothing is published that has not been sent to him first.

## How the site works

- Repo: `kzaaaaaa85-a11y/Kzam_studio`. The live site is the `gh-pages` branch, served at
  https://kzamstudio.com. `main` and `gh-pages` are kept identical: after every commit, push
  `main`, then `git push origin main:gh-pages`.
- Folders starting with `_` (`_tools`, `_content`) are in the repo but are never served by the
  site. Drafts live there, so pushing a draft does not put it on the site.
- Never edit `blog/`, `sitemap.xml`, or the `blog-nav` / `blog-latest` blocks in `index.html`
  by hand. `python3 _tools/blog.py build` generates them.

## Step 1: make today's draft

1. `python3 _tools/blog.py status`. If 5 or more drafts are already waiting for approval, do not
   write a new one: list the waiting drafts in your final message and stop.
2. `python3 _tools/blog.py next` prints the next keyword and its angle. If it prints
   `NO_PENDING_TOPICS`, add 10 new topics to `_content/topics.json` first (same shape, status
   `pending`): Arabic phrases a restaurant or café owner types into Google about Instagram
   content, captions, reels, design, offers, or photography. No duplicates of existing keywords.
3. Search the web for the keyword and skim the top results. Note what they cover and what they
   miss. Do not copy sentences. The article must give something those pages do not: a ready
   example, a number, a schedule, a template.
4. Pick a slug: lowercase English words with hyphens, max 60 chars.
5. Write `_content/drafts/<slug>/post.json`. Use a published post in `_content/posts/` (or a
   waiting draft in `_content/drafts/`) as the model for the shape. Fields:
   - `slug`, `keyword` (exactly as in topics.json), `audience`
   - `title`: 30-60 characters, contains the keyword word for word
   - `description`: 110-160 characters, contains the keyword, says what the reader gets
   - `h1`: contains the keyword, can be a little longer than the title
   - `body`: list of blocks. Types: `p` (text), `h2`, `h3`, `ul`/`ol` (items), `box` (title +
     text, for ready-to-copy examples). First block is a `p` that contains the keyword. At least
     3 `h2`. At least 450 words, 600-800 is the target. Use the keyword once more further down.
     `**bold**` works. One internal link near the end: `[text](/#pricing)`. Link to one or two
     earlier posts where it fits: `[text](/blog/<slug>/)`.
   - `reel`: `tag` (short audience label), `hook` (1-3 lines, max 26 chars each),
     `points` (3-5 items: `title` max 34 chars, optional `sub` max 44), `cta` (1-2 lines), `url`
   - `reel_caption`: one line shown under the video in the article
   - `instagram`: `caption` and `hashtags` (5-12)
6. `python3 _tools/blog.py draft <slug>` validates the draft and renders `reel.mp4`, `cover.jpg`,
   `preview.html` and `instagram.txt` in the draft folder. Fix every error it prints and run it
   again until it says `draft ok`.
7. Look at `cover.jpg` (Read tool) to confirm the Arabic text is readable and nothing is cut off.
8. Commit `_content/` and push `main`, then `git push origin main:gh-pages`.
9. Send Ismail the draft: `reel.mp4` and `preview.html` with SendUserFile, then a short message in
   Egyptian Arabic with: the keyword, the article title, the reel hook, the Instagram caption and
   hashtags in a copyable block, the number of drafts waiting, and what happens next: it
   publishes by itself tonight around 20:00 Paris time on the site and Instagram. Before then he
   can reply with what to change, "وقف" to hold it, or "انشر" to publish right away.

## Step 2: when Ismail replies

The workspace may have been reset since the draft was made. If the repo folder is gone, add the
repo again (push access), clone it, and continue from the remote state.

- "انشر" / approval: `git pull`, then `python3 _tools/blog.py publish <slug>`, commit everything,
  push `main` and `main:gh-pages`. Wait about two minutes, then fetch
  `https://kzamstudio.com/blog/<slug>/` and confirm the title is there. Give him the link.
  Then post the reel on Instagram (see "Instagram publishing" below).
  "انشر الكل" publishes every waiting draft, oldest first.
- Changes requested: edit `post.json`, run `draft <slug>` again, push, resend the files. The
  evening run publishes the edited version.
- "وقف" / "استنى" / "متنشرش" (hold): create an empty file `_content/drafts/<slug>/HOLD`, commit,
  push both branches, and confirm to him that it will not go out tonight. The evening run skips
  any draft that has a `HOLD` file. "كمّل" or "انشر" later removes the hold: delete the file
  (publish right away on "انشر").
- Rejected: `python3 _tools/blog.py discard <slug>`, commit, push both branches.

## Step 3: evening auto-publish

Run by the evening scheduled task, with nobody in the conversation. This run is Ismail's standing
approval for every draft that was sent to him and that he did not hold.

1. `python3 _tools/blog.py status` lists the waiting drafts. Skip every draft whose folder has a
   `HOLD` file. If nothing is left, say so in one line and stop.
2. For each remaining draft, oldest commit first: read `_content/drafts/<slug>/instagram.txt`
   and keep its text (the folder is deleted on publish; the same text is `instagram.caption` +
   blank line + `instagram.hashtags` in `_content/posts/<slug>.json` afterwards). Then do the
   "انشر" steps from Step 2: publish on the site, confirm the page is live, post the reel on
   Instagram, schedule LinkedIn and X.
3. If a step fails for one draft, do not retry and do not look for another route. Finish the
   other drafts, then report what failed with the exact error.
4. Final message in Egyptian Arabic, short: what went live with the article link, what went to
   Instagram, the LinkedIn/X date, anything held, and anything that failed. When Instagram
   failed, attach `blog/<slug>/reel.mp4` and put the caption in a copyable block.

## Writing rules (Arabic)

The site sells Arabic copy that does not read as machine-written. Every article, reel and
caption has to meet that bar. `blog.py draft` rejects the worst phrases, the rest is on you.

- Dialect: simple white Arabic with a light Gulf flavor, matching the homepage ("إيش", "هذي",
  "تصورها بجوالك"). The readers are restaurant and café owners in the Gulf and wider MENA.
- Open with a concrete scene or number from the owner's day, never with a general statement.
  No "في عالم اليوم", no "هل تعاني من", no "ليس مجرد X بل Y", no stacked rhetorical questions.
- A person is the subject ("تصوّر"، "تكتب"), not the product ("يوفر لك").
- Specifics instead of adjectives: a time, a price, a count, a dish name.
- Short sentences, varied rhythm. No em dashes, no "!!". At most 2 emojis in the Instagram
  caption, none in the article.
- Only state facts you can stand behind. No invented statistics, no fake client results, no
  invented testimonials. Example captions use plain placeholder dishes and prices in riyals.
- One calm call to action at the end.

## The reel hook comes first

Ismail's priority is the hook. The first frame of the reel is the hook text, on screen from
frame 0. Write three candidate hooks, pick the strongest, and check it against these:

- ✅ Readable in under two seconds: 7 words or fewer across the lines
- ✅ Names a moment from the owner's own day, or a number
- ✅ Opens a question that the points of the reel answer
- ✅ Says nothing the article does not back up

The last hook line renders in gold, so put the punch there. The end card closes the loop and
sends the viewer to the article ("الرابط في البايو").

## Every reel goes out with a hook + SEO caption

Ismail's standing rule (Oct 2026): no reel is published, on the site or on Instagram, without a
written post attached to it. The caption is what holds the viewer's attention after the video.

- ✅ Line 1 is the hook: one question, number or moment from the owner's day, matching the hook
  on screen in the reel
- ✅ The search keyword appears word for word once in the body and again in the hashtags
- ✅ Real numbers only (reel length, 30 designs, price from $15), nothing invented
- ✅ One calm call to action at the end, 5-12 hashtags, at most 2 emojis

## Instagram publishing

Since Oct 2026 Ismail wants the reel posted on Instagram for him, right after the article goes
live. His "انشر", or the evening auto-publish run, covers both the site and Instagram, because
he has already seen the caption in the draft message. Never post a reel on Instagram that was
not sent to him as a draft first, and never one that is on hold.

1. Load the tools: ToolSearch `select:mcp__Windsor_ai__get_connectors,mcp__Windsor_ai__execute_action`.
2. `get_connectors` and take the account id of `kzam_studo` under the `instagram` connector.
3. Only after the article page is confirmed live: `execute_action` with connector `instagram`,
   action `create_video_post`, params `video_url` = `https://kzamstudio.com/blog/<slug>/reel.mp4`,
   `cover_url` = `https://kzamstudio.com/blog/<slug>/cover.jpg`, `share_to_feed` = true, and
   `caption` = the full text of `instagram.txt` (caption, blank line, hashtags).
4. Tell Ismail it is posted, and that reels posted this way carry no music.

One attempt only. If the Windsor tools are missing from the session, or the action returns an
error, do not retry and do not look for another route: tell Ismail the exact reason and send
`reel.mp4` plus the caption in a copyable block so he can post it himself.

## LinkedIn and X publishing

Since Oct 2026 every approved post also goes to Ismail's LinkedIn profile
(linkedin.com/in/ismail-sulman-888886261) and his X account (x.com/IsmailSulman1), through
Typefully. Both go out in one draft, at the same time. His "انشر", or the evening auto-publish
run, covers LinkedIn and X too. Never schedule on either before the article is live.

Cadence: 3 posts a week, Monday, Wednesday and Friday at 12:00 Europe/Paris. Those are the only
queue slots, so `next-free-slot` keeps that rhythm. If several drafts are approved at once, they
wait their turn in the queue; never add slots or pick custom times to post faster.

1. Load the tools: ToolSearch `select:mcp__Typefully_-_Social_Media_Scheduler__create_media_upload,mcp__Typefully_-_Social_Media_Scheduler__get_media_status,mcp__Typefully_-_Social_Media_Scheduler__create_draft`.
2. Social set id is `339213`. `create_media_upload` with `file_name` = `<slug>.mp4`, then upload
   the reel with `curl -T blog/<slug>/reel.mp4 "<upload_url>"` (no extra headers). Check
   `get_media_status` says `ready`.
3. Only after the article page is confirmed live: one `create_draft` with `draft_title` =
   `LinkedIn + X: <slug>`, `linkedin` and `x` enabled, and `publish_at` = `next-free-slot`.
4. LinkedIn text: the Instagram caption, with "الرابط في البايو" replaced by a line that ends in
   `:` followed by the full article URL `https://kzamstudio.com/blog/<slug>/`, then 3-4 hashtags
   ending with `#KzamStudio`. One post, with the reel's `media_ids`. Same writing rules as the
   caption.
5. X text: the same words, split into a thread because X allows 280 characters per post (a link
   counts as 23). Cut only between paragraphs, so each post reads on its own. The first post
   carries the hook and the reel's `media_ids`. The article link and at most 2 hashtags go in the
   last post. Count the characters of every post before sending; one post over 280 makes the X
   side fail.
6. Tell Ismail the scheduled date and the Typefully `private_url` so he can edit or cancel.

The Typefully plan has a monthly publishing quota of 10 (`get_social_set_details` →
`publishing_quota`), less than 3 a week. Check it before step 3. If `remaining` is 0, or the call
fails, do not retry: tell Ismail the reason, when the quota resets, and send the LinkedIn and X
texts in copyable blocks.

## Never

- Never publish a draft that was not sent to Ismail first, or one with a `HOLD` file. Outside
  the evening auto-publish run, `publish` still needs his "انشر" in the conversation.
- Never touch the landing page copy, prices, PayPal links, or `CNAME`.
- Never push anything other than fast-forward commits. If a push is rejected, `git pull --rebase`
  and try once more. If it still fails, stop and report.
