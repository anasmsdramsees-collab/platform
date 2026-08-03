#!/usr/bin/env bash
# Builds a static export for GitHub Pages, which has no server runtime.
# The Sina API route needs a Node server, so it's moved out of app/ for the
# duration of this build (and restored afterwards no matter how the build ends)
# rather than being deployed as a broken route.
set -u

APP_DIR="src/app"
API_DIR="$APP_DIR/api"
API_STASH="$APP_DIR/_api_disabled_for_static_export"

restore_api() {
  if [ -d "$API_STASH" ]; then
    rm -rf "$API_DIR"
    mv "$API_STASH" "$API_DIR"
  fi
}
trap restore_api EXIT

if [ -d "$API_DIR" ]; then
  mv "$API_DIR" "$API_STASH"
fi

STATIC_EXPORT=1 npx next build
