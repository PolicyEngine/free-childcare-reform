/** @type {import('next').NextConfig} */
const basePath = "/uk/free-childcare-reform";

const nextConfig = {
  reactStrictMode: true,
  transpilePackages: ["@policyengine/design-system"],
  // Served through the policyengine.org multizone rewrite at /uk/free-childcare-reform,
  // so pages and /_next assets must resolve under that prefix.
  basePath,
  // Next.js only auto-prefixes next/link, next/image and static imports. Raw
  // fetch() calls and plain <img src> need this explicitly.
  env: {
    NEXT_PUBLIC_BASE_PATH: basePath,
  },
};

module.exports = nextConfig;
