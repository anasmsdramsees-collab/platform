// next/image with `unoptimized: true` (used for the static GitHub Pages export)
// does not auto-prefix its `src` with `basePath`, unlike normal server builds.
// Any raw "/..." asset path passed to <Image> needs this wrapper so it still
// resolves once the site is served under /syntrasmart.
export const basePath = process.env.NEXT_PUBLIC_BASE_PATH ?? "";

export function assetPath(path: string): string {
  return `${basePath}${path}`;
}
