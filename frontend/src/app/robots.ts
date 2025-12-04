import { MetadataRoute } from 'next';

export default function robots(): MetadataRoute.Robots {
  const baseUrl = process.env.NEXT_PUBLIC_FRONTEND_URL || 'https://tkxn.org';

  return {
    rules: [
      {
        userAgent: '*',
        allow: '/',
        disallow: [
          '/api/',
          '/admin/',
          '/me/',
          '/profile/',
          '/dashboard/',
          '/transactions/',
          '/wallet/',
          '/deposit/',
          '/funds/',
          '/referrals/',
          '/details/',
          '/confirm-withdrawal/',
          '/verify-email/',
          '/login-success/',
        ],
      },
    ],
    sitemap: `${baseUrl}/sitemap.xml`,
  };
}

