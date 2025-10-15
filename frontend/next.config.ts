/** @type {import('next').NextConfig} */
const nextConfig = {
  webpack: (config: any) => {
    config.watchOptions = {
      poll: 3000,
      aggregateTimeout: 600,
      ignored: ['**/node_modules', '**/.git', '**/.next'],
    };
    
    return config;
  },
  reactStrictMode: false,
  compress: true,
  generateEtags: false,
  images: {
    remotePatterns: [
      {
        protocol: 'https',
        hostname: 'images.unsplash.com',
      },
      {
        protocol: 'https',
        hostname: 'tkxn.org',
      },
      {
        protocol: 'http',
        hostname: 'localhost',
        port: '8000',
        pathname: '/media/**',
      },
    ],
    deviceSizes: [640, 750, 828, 1080, 1200, 1920, 2048, 3840],
    imageSizes: [16, 32, 48, 64, 96, 128, 256, 384],
    domains: ['localhost'],
  },
  async rewrites() {
    const apiUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'https://tkxn.org';
    
    return [
      {
        source: '/media/:path*',
        destination: `${apiUrl}/media/:path*`,
      },
      {
        source: '/accounts/google/login/',
        destination: `${apiUrl}/accounts/google/login/`,
      },
      {
        source: '/accounts/yandex/login/',
        destination: `${apiUrl}/accounts/yandex/login/`,
      },
      {
        source: '/accounts/telegram/login/',
        destination: `${apiUrl}/accounts/telegram/login/`,
      },
      {
        source: '/accounts/google/login/callback/',
        destination: `${apiUrl}/accounts/google/login/callback/`,
      },
      {
        source: '/accounts/yandex/login/callback/',
        destination: `${apiUrl}/accounts/yandex/login/callback/`,
      },
      {
        source: '/api/:path*',
        destination: `${apiUrl}/api/:path*`,
      },
    ];
  },
  trailingSlash: true,
  typescript: {
    ignoreBuildErrors: true,
  },
  eslint: {
    ignoreDuringBuilds: true,
  },
};

export default nextConfig;
