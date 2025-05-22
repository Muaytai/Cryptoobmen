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
        hostname: 'kripto-obmen.com',
      },
    ],
    deviceSizes: [640, 750, 828, 1080, 1200, 1920, 2048, 3840],
    imageSizes: [16, 32, 48, 64, 96, 128, 256, 384],
  },
  async rewrites() {
    const apiUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'https://kripto-obmen.com';
    
    return [
      {
        source: '/accounts/:provider/login',
        destination: `${apiUrl}/accounts/:provider/login`,
      },
      {
        source: '/accounts/:provider/login/',
        destination: `${apiUrl}/accounts/:provider/login/`,
      },
      {
        source: '/accounts/:path*',
        destination: `${apiUrl}/accounts/:path*`,
      },
      {
        source: '/api/:path*',
        destination: `${apiUrl}/api/:path*`,
      },
      {
        source: '/api/:path*/',
        destination: `${apiUrl}/api/:path*/`,
      },
    ];
  },
  trailingSlash: true,
};

export default nextConfig;
