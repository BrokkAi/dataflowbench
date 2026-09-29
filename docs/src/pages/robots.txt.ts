import type { APIRoute } from 'astro';

// Every page is public; the sitemap Starlight generates lists them. Built
// from the configured site so a preview build points at its own sitemap.
export const GET: APIRoute = ({ site }) => {
  const sitemap = new URL(`${import.meta.env.BASE_URL.replace(/\/?$/, '/')}sitemap-index.xml`, site);
  return new Response(`User-agent: *\nAllow: /\n\nSitemap: ${sitemap.href}\n`);
};
