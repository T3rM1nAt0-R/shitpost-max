"use client";

import { useEffect } from "react";

export default function Track404() {
  useEffect(() => {
    const send = () => window.umami?.track("404", { path: location.pathname.slice(0, 80) });
    if (window.umami) send();
    else if (document.readyState === "complete") setTimeout(send, 1000);
    else addEventListener("load", send, { once: true });
  }, []);
  return null;
}
