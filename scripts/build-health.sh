#!/usr/bin/env bash
# Build command for the SYLTRA HEALTH Pages project (health.syltraone.com).
# Same static export as the main site, then overwrite the root files with
# health-specific sitemap / robots / llms / _redirects.
set -eu
bash scripts/build-pages.sh
node scripts/gen-health-root.mjs
