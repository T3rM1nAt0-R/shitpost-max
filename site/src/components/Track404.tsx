"use client";

import { useEffect } from "react";

export default function Track404() {
  useEffect(() => {
    const send = () => window.umami?.track("404", { path: location.pathname });
    if (window.umami) send();
    else addEventListener("load", send, { once: true });
  }, []);
  return null;
}
