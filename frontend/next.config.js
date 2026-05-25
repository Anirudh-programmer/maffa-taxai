/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  images: {
    domains: ['img.clerk.com', 'images.clerk.dev', 'avatars.githubusercontent.com'],
  },
  experimental: {
    serverActions: { allowedOrigins: ['localhost:3000'] },
    // Eagerly compile all pages to eliminate first-visit 10s delay
    optimisticClientCache: true,
  },
  eslint: {
    ignoreDuringBuilds: true,
  },
  typescript: {
    ignoreBuildErrors: true,
  },
  // Compress responses
  compress: true,
  // Reduce memory usage and speed up dev compilation
  onDemandEntries: {
    // Keep pages in memory for 120 seconds (default 15s)
    maxInactiveAge: 120 * 1000,
    // Keep up to 10 pages in memory
    pagesBufferLength: 10,
  },
}

module.exports = nextConfig
