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
