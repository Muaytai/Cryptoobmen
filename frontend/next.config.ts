/** @type {import('next').NextConfig} */
const nextConfig = {
  webpack: (config: any) => {
    config.watchOptions = {
      poll: 1000,
      aggregateTimeout: 300,
      ignored: ['**/node_modules'],
    };
    return config;
  },
  images: {
    remotePatterns: [
      {
        protocol: 'https',
        hostname: 'images.unsplash.com',
      },
    ],
  },
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://localhost:8000/api/:path*/', // Добавляем слэш в конце каждого запроса
      },
      {
        source: '/api/:path*/',
        destination: 'http://localhost:8000/api/:path*/', // Явно обрабатываем URL с завершающим слэшем
      },
    ];
  },
};

export default nextConfig;
