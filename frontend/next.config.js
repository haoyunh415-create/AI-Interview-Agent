/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'export',
  distDir: 'out',
  images: { unoptimized: true },
  compiler: {
    removeConsole: process.env.NODE_ENV === 'production' ? { exclude: ['error', 'warn'] } : false,
  },
  // Point turbopack to the frontend directory
  turbopack: {
    root: __dirname,
  },
  experimental: {
    optimizePackageImports: [
      'recharts',
      'react-markdown',
      'react-syntax-highlighter',
      'zustand',
      '@tanstack/react-query',
    ],
  },
}

// Bundle analysis (run: ANALYZE=true npm run build)
const withBundleAnalyzer = process.env.ANALYZE
  ? require('@next/bundle-analyzer')({ enabled: true, openAnalyzer: true })
  : (config) => config

module.exports = withBundleAnalyzer(nextConfig)
