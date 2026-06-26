import type { APIRoute } from "astro";
import { SITE_TITLE, SITE_DESCRIPTION } from "../lib/config/site";
import { loadHomepageDigest } from "../lib/content/getLatestDigest";

export const GET: APIRoute = async ({ site }) => {
  const feedUrl = site ? new URL("/feed.xml", site).toString() : "https://example.com/feed.xml";
  const siteUrl = site ? site.toString() : "https://example.com/";

  const result = await loadHomepageDigest();

  let items = "";

  if (result.kind === "success") {
    const { digest } = result;
    items = digest.entries
      .map((entry) => {
        return `
      <item>
        <title><![CDATA[${entry.headline}]]></title>
        <description><![CDATA[${entry.summary}]]></description>
        <pubDate>${new Date(digest.published_at).toUTCString()}</pubDate>
        <guid>${feedUrl}#${entry.cluster_id}</guid>
      </item>`;
      })
      .join("\n");
  }

  const rss = `<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>${SITE_TITLE}</title>
    <description>${SITE_DESCRIPTION}</description>
    <link>${siteUrl}</link>
    <atom:link href="${feedUrl}" rel="self" type="application/rss+xml" />
    <language>en</language>
    <lastBuildDate>${new Date().toUTCString()}</lastBuildDate>${items}
  </channel>
</rss>`;

  return new Response(rss.trim(), {
    headers: {
      "Content-Type": "application/xml; charset=utf-8"
    }
  });
};
