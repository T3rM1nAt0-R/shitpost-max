import type { CSSProperties } from "react";
import { formatValuation, type FleetServiceStats } from "@/lib/fleet";
import { NEON } from "./neon";

interface Props {
  service: FleetServiceStats;
  rank: number;
}

/** Static server-rendered card. Tilt, votes, sorting and search are delegated (FeedGrid / FeedControls). */
export default function ServiceCard({ service: s, rank }: Props) {
  return (
    <article
      className="fx-card"
      data-slug={s.slug}
      data-base-score={s.baseScore}
      data-valuation={s.valuation}
      data-search={`${s.name} ${s.slug} ${s.tagline}`.toLowerCase()}
      style={{ "--accent": NEON[rank % NEON.length] } as CSSProperties}
    >
      <div className="spm-fx">
        <div className="spm-tilt">
          <div aria-hidden className="spm-glare" />
          <div className="flex items-start justify-between gap-3">
            <span className="spm-emoji">{s.emoji}</span>
            <span className="spm-badge">
              <span data-rank>#{rank + 1}</span> · {s.ticker}
            </span>
          </div>
          <h3 className="spm-name">
            <a href={s.url} target="_blank" rel="noopener noreferrer">
              {s.name}
            </a>
          </h3>
          <p className="spm-tag">{s.tagline}</p>
          <dl className="spm-dl">
            <div>
              <dt>Valuation</dt>
              <dd className="text-emerald-300" data-money>
                {formatValuation(s.valuation)}
              </dd>
            </div>
            <div>
              <dt>Engineers replaced</dt>
              <dd className="text-fuchsia-300" data-money>
                {s.engineersReplaced.toLocaleString("en-US")}
              </dd>
            </div>
          </dl>
          <div className="spm-foot">
            <div className="spm-votes">
              <button type="button" data-vote="1" aria-label={`Upvote ${s.name}`} className="spm-vb spm-up">
                ▲
              </button>
              <span className="spm-score" data-score data-money>
                {s.baseScore.toLocaleString("en-US")}
              </span>
              <button type="button" data-vote="-1" aria-label={`Downvote ${s.name}`} className="spm-vb spm-down">
                ▼
              </button>
            </div>
            <a href={s.url} target="_blank" rel="noopener noreferrer" className="spm-src">
              source ↗
            </a>
          </div>
        </div>
      </div>
    </article>
  );
}
