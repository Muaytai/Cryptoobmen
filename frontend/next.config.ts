import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* config options here */
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
