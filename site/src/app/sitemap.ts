import type { MetadataRoute } from "next";

export const dynamic = "force-static";

const LAST_MODIFIED = new Date();

export default function sitemap(): MetadataRoute.Sitemap {
  return [
    { url: "https://shitpostmax.com/", lastModified: LAST_MODIFIED, changeFrequency: "daily", priority: 1 },
    { url: "https://shitpostmax.com/generator/", lastModified: LAST_MODIFIED, changeFrequency: "weekly", priority: 0.8 },
  ];
}
