import { getFleetWithStats } from "@/lib/fleet";
import FeedControls from "./FeedControls";
import FeedGrid from "./FeedGrid";
import FeedCards from "./FeedCards";
import LiveFeed from "./LiveFeed";
import "./feed.css";

const GRID_ID = "feed-grid";
const EMPTY_ID = "feed-empty";

/** Feed shell (server). Cards are hook-free static markup; FeedControls/FeedGrid add behaviour without re-rendering them. */
export default function Feed() {
  const fleet = getFleetWithStats();

  return (
    <section id="feed" className="mx-auto max-w-7xl scroll-mt-8 px-4 pb-24">
      <div className="mb-8 text-center">
        <h2 className="glitch text-4xl font-black uppercase tracking-tight text-white sm:text-6xl" data-text="The Feed">
          The Feed
        </h2>
        <p className="mt-3 text-zinc-400">
          <span data-money>{fleet.length}</span> portfolio companies. Each one a monument to solving nothing at
          scale. Vote like it matters (it does not).
        </p>
      </div>

      <FeedControls gridId={GRID_ID} emptyId={EMPTY_ID} />

      <p id={EMPTY_ID} hidden className="py-20 text-center text-xl text-zinc-400">
        No results. I&apos;ll just acquire a company called &ldquo;<span data-query />&rdquo;. Done. You&apos;re
        welcome.
      </p>
      <FeedGrid id={GRID_ID}>
        <FeedCards />
      </FeedGrid>
      <LiveFeed gridId={GRID_ID} />
    </section>
  );
}
