"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const LINKS = [
  { href: "/", label: "Feed" },
  { href: "/generator", label: "Generator" },
];

/** Sticky nav under the ticker. Links glitch on hover. */
export default function NavBar() {
  const pathname = usePathname();
  return (
    <nav className="sticky top-8 z-40 border-b border-white/10 bg-black/60 backdrop-blur-md">
      <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-4 py-3">
        <Link
          href="/"
          className="glitch rainbow-text font-[family-name:var(--font-display)] text-xl sm:text-2xl"
          data-text="SHITPOSTMAX"
        >
          SHITPOSTMAX
        </Link>
        <ul className="flex items-center gap-2 sm:gap-4">
          {LINKS.map(({ href, label }) => {
            const active = href === "/" ? pathname === "/" : pathname.startsWith(href);
            return (
              <li key={href}>
                <Link
                  href={href}
                  aria-current={active ? "page" : undefined}
                  data-text={label}
                  className={`nav-link glitch-hover rounded-md px-3 py-1.5 font-[family-name:var(--font-display)] text-sm uppercase tracking-wider transition-colors sm:text-base ${
                    active ? "neon text-[var(--lime)]" : "text-white/80 hover:text-[var(--cyan)]"
                  }`}
                >
                  {label}
                </Link>
              </li>
            );
          })}
        </ul>
      </div>
    </nav>
  );
}
