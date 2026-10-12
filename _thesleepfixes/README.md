# thesleepfixes.com (ClickBank YU SLEEP funnel)

Not part of kzamstudio.com. Kept here only so the files persist; the leading `_` keeps
this folder off the agency site.

- `site/` is the full static site for thesleepfixes.com: `index.html` (landing page with
  the opt-in form), `privacy.html`, `the-5-sleep-fixes.pdf` (the free guide).
- `guide/guide.html` is the source of the PDF (render with Playwright, Letter size).
- Domain thesleepfixes.com bought 12 Oct 2026 on WordPress.com (account kzamsulaman),
  nameservers still WordPress.com. Needs its own GitHub repo + Pages, then DNS records.
- The form posts to Kit (kit.com). Replace `KIT_FORM_ID` in `site/index.html` with the
  real Kit form ID once Ismail has created the Kit account. MailerLite is not an option:
  its terms ban affiliate marketing.
- `contact@thesleepfixes.com` is referenced in privacy.html: set up a free email forward
  on WordPress.com before launch.

## Status 12 Oct 2026 (evening)
- Live repo: github.com/kzaaaaaa85-a11y/thesleepfixes (main, GitHub Pages on, CNAME thesleepfixes.com).
  The Claude GitHub app now has access to it. The canonical site files live there, not here.
- Ismail chose the Canva "night bedroom" hero (Canva media MAHXzTDBpKo). images/hero.jpg is still
  the 200px thumbnail; the full 1680x944 file must be pulled through the built-in browser
  (sandbox can't reach media.canva.com) and pushed to the live repo.
- TODO DNS on WordPress.com (account kzamsulaman): A @ 185.199.108.153, .109.153, .110.153,
  .111.153 and CNAME www -> kzaaaaaa85-a11y.github.io. The wpcom domain-update-dns-records MCP
  ability was refused even after Ismail enabled all write abilities; retry in a new session.
  Then enable "Enforce HTTPS" in the repo's Pages settings.
- TODO Kit account (Ismail creates it), then replace KIT_FORM_ID in index.html.
