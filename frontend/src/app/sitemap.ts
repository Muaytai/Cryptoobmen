import { MetadataRoute } from 'next';

export default function sitemap(): MetadataRoute.Sitemap {
  const baseUrl = process.env.NEXT_PUBLIC_FRONTEND_URL || 'https://tkxn.org';

  // Публичные страницы для индексации
  const routes = [
    '',
    '/about',
    '/contacts',
    '/faq',
    '/reviews',
    '/support',
    '/feedback',
    '/exchange',
    '/login',
    '/register',
    '/agreement',
    '/privacy',
    '/terms',
    '/aml',
    '/security',
  ];

  const sitemapEntries: MetadataRoute.Sitemap = routes.map((route) => ({
    url: `${baseUrl}${route}`,
    lastModified: new Date(),
    changeFrequency: route === '' ? 'daily' : 'weekly',
    priority: route === '' ? 1.0 : route === '/exchange' ? 0.9 : 0.8,
  }));

  return sitemapEntries;
}

