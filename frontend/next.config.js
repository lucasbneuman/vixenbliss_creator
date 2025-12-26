/** @type {import('next').NextConfig} */
const nextConfig = {
  images: {
    domains: ['cdn.vixenbliss.com', 'pub-*.r2.dev'],
  },
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  },
}

module.exports = nextConfig
