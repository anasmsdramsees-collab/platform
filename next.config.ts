import type { NextConfig } from "next";

const isStaticExport = process.env.STATIC_EXPORT === "1";
// Custom domain (syltraone.com) serves from the root — no basePath needed.
const basePath = "";

const nextConfig: NextConfig = {
  env: {
    NEXT_PUBLIC_BASE_PATH: basePath,
  },
  ...(isStaticExport
    ? {
        output: "export",
        basePath,
        assetPrefix: basePath,
        trailingSlash: true,
        images: { unoptimized: true },
      }
    : {}),
};

export default nextConfig;
