import type { MetadataRoute } from "next";

export const dynamic = "force-static";

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "SHITPOSTMAX",
    short_name: "SPM",
    description: "The fanciest and most shitposty website ever. Funded by all billionaires combined.",
    start_url: "/",
    display: "standalone",
    background_color: "#000000",
    theme_color: "#ff00aa",
    icons: [
      { src: "/icon", sizes: "32x32", type: "image/png" },
      { src: "/apple-icon", sizes: "180x180", type: "image/png" },
    ],
  };
}
