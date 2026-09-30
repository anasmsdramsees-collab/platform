#!/usr/bin/env bash
# Build command for the SYLTRA HEALTH Cloudflare Pages project ONLY.
# (The main syltraone.com project keeps using `STATIC_EXPORT=1 npx next build`.)
#
# Set this project's Build command to:  bash scripts/build-health.sh
#
# It builds the static export, then overwrites sitemap.xml + robots.txt with
# health-subdomain versions, and writes the root->/(locale)/health redirects.
set -e

STATIC_EXPORT=1 npx next build

# Health-specific sitemap.xml + robots.txt (health.syltraone.com).
node scripts/health-sitemap.mjs

# Root of the subdomain opens the HEALTH home.
printf '/  /en/health  302\n/en  /en/health  302\n/ar  /ar/health  302\n' > out/_redirects
