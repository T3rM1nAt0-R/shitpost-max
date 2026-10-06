"use client";

import { useEffect } from "react";
import { usePathname } from "next/navigation";
import { PUBLIC_HOSTS, UMAMI_SRC, UMAMI_WEBSITE_ID } from "@/lib/analytics";

type Umami = { track: (name: string, data?: Record<string, string | number>) => void };
declare global {
  interface Window {
    umami?: Umami;
  }
}

// Guarded like site-analytics: queue until the Umami script has loaded.
const track = (name: string, data?: Record<string, string | number>) => {
  if (window.umami) window.umami.track(name, data);
  else if (document.readyState === "complete") setTimeout(() => window.umami?.track(name, data), 1000);
  else window.addEventListener("load", () => window.umami?.track(name, data), { once: true });
};

// Loads Umami on the public host only (dev-test is Access-only and never counted),
// tags outbound links, and reports scroll depth. Page-level 404s are tracked in not-found.
const seen = new Set<number>();

export default function Analytics() {
  const pathname = usePathname();
  useEffect(() => {
    seen.clear();
  }, [pathname]);

  useEffect(() => {
    if (!UMAMI_WEBSITE_ID || !PUBLIC_HOSTS.includes(location.hostname)) return;
    if (localStorage.getItem("umami.disabled")) return;

    const s = document.createElement("script");
    s.defer = true;
    s.src = UMAMI_SRC;
    s.dataset.websiteId = UMAMI_WEBSITE_ID;
    s.dataset.domains = PUBLIC_HOSTS.join(",");
    document.head.appendChild(s);

    const onClick = (e: MouseEvent) => {
      const a = (e.target as Element | null)?.closest?.("a[href]") as HTMLAnchorElement | null;
      if (!a || a.hostname === location.hostname || !/^https?:$/.test(a.protocol)) return;
      track("outbound-click", { url: a.origin + a.pathname }); // no query or hash
    };
    document.addEventListener("click", onClick);

    const onScroll = () => {
      const max = document.documentElement.scrollHeight - innerHeight;
      if (max <= 0) return;
      const pct = (scrollY / max) * 100;
      for (const mark of [25, 50, 75, 100]) {
        if (pct >= mark - 1 && !seen.has(mark)) {
          seen.add(mark);
          track("scroll-depth", { pct: mark });
        }
      }
    };
    addEventListener("scroll", onScroll, { passive: true });
    return () => {
      document.removeEventListener("click", onClick);
      removeEventListener("scroll", onScroll);
    };
  }, []);
  return null;
}
