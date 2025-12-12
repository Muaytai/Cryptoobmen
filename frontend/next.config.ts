<<<<<<< HEAD
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
      // Rewrite только специфичные API пути бэкенда
      // Next.js API routes (/api/reviews, /api/auth/callback, /api/feedback) обрабатываются локально
      {
        source: '/api/accounts/:path*',
        destination: `${apiUrl}/api/accounts/:path*`,
      },
      {
        source: '/api/crypto/:path*',
        destination: `${apiUrl}/api/crypto/:path*`,
      },
      {
        source: '/api/transactions/:path*',
        destination: `${apiUrl}/api/transactions/:path*`,
      },
      {
        source: '/api/auth/login',
        destination: `${apiUrl}/api/auth/login`,
      },
      {
        source: '/api/auth/logout',
        destination: `${apiUrl}/api/auth/logout`,
      },
      {
        source: '/api/auth/user',
        destination: `${apiUrl}/api/auth/user`,
      },
      {
        source: '/api/auth/registration/:path*',
        destination: `${apiUrl}/api/auth/registration/:path*`,
      },
      {
        source: '/api/auth/password/:path*',
        destination: `${apiUrl}/api/auth/password/:path*`,
      },
      {
        source: '/api/auth/google',
        destination: `${apiUrl}/api/auth/google`,
      },
      {
        source: '/api/auth/yandex',
        destination: `${apiUrl}/api/auth/yandex`,
      },
      {
        source: '/api/token/:path*',
        destination: `${apiUrl}/api/token/:path*`,
      },
      {
        source: '/api/schema/:path*',
        destination: `${apiUrl}/api/schema/:path*`,
      },
      {
        source: '/api/docs/:path*',
        destination: `${apiUrl}/api/docs/:path*`,
      },
      {
        source: '/api/redoc/:path*',
        destination: `${apiUrl}/api/redoc/:path*`,
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
=======
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
>>>>>>> 15289855a991ed48da9be2cf9124ebfb7d590251
