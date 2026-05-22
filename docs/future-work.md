# Future Work

This file tracks ideas that are intentionally outside the current pilot scope.

## Public KB Ingest Scraper

Status: future idea only; do not add before pilot without explicit approval.

A public knowledge-base ingest scraper could be considered after pilot handoff as a non-runtime review aid. It should not become part of the Flask app, routing flow, retrieval path, or deployment process.

Safety requirements if this idea is revisited:

- Keep it as a non-runtime tool only.
- Save scraped pages as candidate output only.
- Do not auto-index scraped content or merge it directly into approved KB files.
- Fail closed when `robots.txt` cannot be read or does not allow fetching.
- Use an explicit approved source list, and review that list before each scrape.
- Treat dependency changes, including scraper libraries, as requiring explicit approval.
- Require human review before any scraped content becomes approved KB content.
