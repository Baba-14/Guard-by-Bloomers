/** @type {import('next').NextConfig} */
const nextConfig = {
  // Keep production artifacts separate from the live dev server cache.
  // This prevents `next build` from invalidating an active `next dev` session.
  distDir: process.env.NEXT_BUILD_DIR || '.next',
  images: { remotePatterns: [{ protocol: 'https', hostname: 'images.unsplash.com' }] }
};
export default nextConfig;
