import type { MetadataRoute } from "next";

export const dynamic = "force-static";

export default function sitemap(): MetadataRoute.Sitemap {
  return [
    { url: "https://shitpostmax.com/", changeFrequency: "daily", priority: 1 },
    { url: "https://shitpostmax.com/generator/", changeFrequency: "weekly", priority: 0.8 },
  ];
}
