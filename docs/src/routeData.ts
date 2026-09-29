/// <reference types="@astrojs/starlight/locals" />

import { defineRouteMiddleware } from '@astrojs/starlight/route-data';

// Archived snapshot pages were written before each page named its release in
// its description, so an early freeze's analyzers page shares one sentence
// with three others and search results cannot tell them apart. The frozen
// pages stay as they were published; only the description their <head>
// carries gains the release it belongs to.
const SNAPSHOT_PAGE = /^snapshots\/v(\d+)-(\d+)-(\d+)(?:\/|$)/;
const DESCRIPTION_TAGS = new Set(['description', 'og:description']);

export const onRequest = defineRouteMiddleware((context) => {
  const route = context.locals.starlightRoute;
  const match = SNAPSHOT_PAGE.exec(route.entry.id);
  const description = route.entry.data.description;
  if (!match || !description) return;
  const version = `v${match[1]}.${match[2]}.${match[3]}`;
  if (description.includes(version)) return;
  for (const tag of route.head) {
    const name = tag.attrs?.name ?? tag.attrs?.property;
    if (tag.tag === 'meta' && typeof name === 'string' && DESCRIPTION_TAGS.has(name)) {
      tag.attrs!.content = `Snapshot ${version}: ${description}`;
    }
  }
});
