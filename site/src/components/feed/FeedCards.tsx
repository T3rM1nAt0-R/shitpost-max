"use client";

import { getFleetWithStats } from "@/lib/fleet";
import ServiceCard from "./ServiceCard";

/**
 * Stateless list of hook-free cards. Rendered from the client bundle (not as RSC output) so the
 * 187 cards are not duplicated as an inlined RSC payload in index.html. It never re-renders:
 * FeedControls / FeedGrid mutate the DOM (order, hidden, CSS vars, text) directly.
 */
const SORTED = [...getFleetWithStats()].sort((a, b) => b.baseScore - a.baseScore);

export default function FeedCards() {
  return SORTED.map((s, i) => <ServiceCard key={s.slug} service={s} rank={i} />);
}
