'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';

import { apiGet } from '@/lib/api';
import type { DailyWarpOut, GalaxyNode } from '@/lib/types';

type Props = {
  userId?: number;
};

type Positioned = GalaxyNode & {
  x: number;
  y: number;
};

// Layout: nodes are grouped by branch_group and stacked vertically within a
// column, giving us the Duolingo-style "path that forks into parallel branches".
function layout(nodes: GalaxyNode[]): Positioned[] {
  const groups: Record<string, GalaxyNode[]> = {};
  for (const node of nodes) {
    const key = node.branch_group ?? 'other';
    (groups[key] ||= []).push(node);
  }

  const groupOrder = Object.keys(groups).sort();
  const colWidth = 240;
  const rowHeight = 100;
  const marginX = 60;
  const marginY = 60;

  const positioned: Positioned[] = [];
  groupOrder.forEach((groupKey, colIdx) => {
    const col = groups[groupKey] ?? [];
    col
      .slice()
      .sort((a, b) => a.rating_min - b.rating_min || a.slug.localeCompare(b.slug))
      .forEach((node, rowIdx) => {
        // zig-zag the x a little to give the "winding Duolingo path" feel
        const wobble = rowIdx % 2 === 0 ? -24 : 24;
        positioned.push({
          ...node,
          x: marginX + colIdx * colWidth + wobble,
          y: marginY + rowIdx * rowHeight,
        });
      });
  });

  return positioned;
}

function domainColor(domain: string): string {
  switch (domain) {
    case 'tactics':
      return '#6ae0ff';
    case 'endgame':
      return '#f0b86e';
    case 'strategy':
      return '#c084fc';
    case 'openings':
      return '#34d399';
    default:
      return '#94a3b8';
  }
}

export function GalaxyPath({ userId = 1 }: Props) {
  const [nodes, setNodes] = useState<GalaxyNode[] | null>(null);
  const [warp, setWarp] = useState<DailyWarpOut | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    Promise.all([
      apiGet<GalaxyNode[]>('/v1/nodes'),
      apiGet<DailyWarpOut>(`/v1/warp/today?user_id=${userId}`).catch(() => null),
    ])
      .then(([n, w]) => {
        if (cancelled) return;
        setNodes(n);
        setWarp(w);
      })
      .catch((e: unknown) => {
        if (!cancelled) setError(e instanceof Error ? e.message : String(e));
      });
    return () => {
      cancelled = true;
    };
  }, [userId]);

  if (error) {
    return (
      <div className="rounded-lg border border-rose-500/40 bg-rose-500/5 p-4 text-sm text-rose-200">
        Galaxy unavailable: {error}
      </div>
    );
  }
  if (!nodes) {
    return <div className="text-sm text-slate-400">Charting the galaxy…</div>;
  }

  const positioned = layout(nodes);
  const highlightedBranch = warp?.node_id
    ? nodes.find((n) => n.id === warp.node_id)?.branch_group ?? null
    : null;
  const highlightedNodeSlug = warp?.node_slug ?? null;

  const slugToPos = new Map(positioned.map((p) => [p.slug, p]));

  const width =
    Math.max(...positioned.map((p) => p.x), 320) + 120;
  const height = Math.max(...positioned.map((p) => p.y), 320) + 100;

  return (
    <div className="w-full" data-testid="galaxy-path">
      <div className="mb-3 flex flex-wrap items-center gap-2 text-xs text-slate-400">
        <span>Legend:</span>
        {(['tactics', 'endgame', 'strategy', 'openings'] as const).map((d) => (
          <span key={d} className="flex items-center gap-1">
            <span
              className="inline-block h-2 w-2 rounded-full"
              style={{ background: domainColor(d) }}
            />
            {d}
          </span>
        ))}
        {highlightedBranch ? (
          <span className="ml-auto text-indigo-300">
            Today&apos;s branch: <strong>{highlightedBranch}</strong>
          </span>
        ) : null}
      </div>
      <div className="overflow-x-auto rounded-lg border border-white/10 bg-galaxy-bg p-2">
        <svg
          viewBox={`0 0 ${width} ${height}`}
          className="min-w-full"
          style={{ minHeight: height }}
        >
          {positioned.map((node) =>
            node.prereq_slugs.map((prereqSlug) => {
              const from = slugToPos.get(prereqSlug);
              if (!from) return null;
              return (
                <line
                  key={`${prereqSlug}->${node.slug}`}
                  x1={from.x}
                  y1={from.y}
                  x2={node.x}
                  y2={node.y}
                  stroke="rgba(255,255,255,0.15)"
                  strokeWidth={1.5}
                />
              );
            }),
          )}
          {positioned.map((node) => {
            const isWeakBranch =
              highlightedBranch !== null && node.branch_group === highlightedBranch;
            const isTarget = node.slug === highlightedNodeSlug;
            const r = isTarget ? 22 : 16;
            const base = domainColor(node.domain);
            return (
              <Link
                key={node.slug}
                href={`/drill?node=${encodeURIComponent(node.slug)}`}
                aria-label={`Open drills for ${node.title}`}
              >
                <g className="cursor-pointer" data-slug={node.slug}>
                  {isTarget ? (
                    <circle
                      cx={node.x}
                      cy={node.y}
                      r={r + 6}
                      fill="none"
                      stroke={base}
                      strokeWidth={2}
                      strokeDasharray="4 3"
                      opacity={0.8}
                    />
                  ) : null}
                  <circle
                    cx={node.x}
                    cy={node.y}
                    r={r}
                    fill={base}
                    opacity={isWeakBranch ? 1 : 0.35}
                    stroke="white"
                    strokeOpacity={isTarget ? 0.9 : 0.2}
                    strokeWidth={isTarget ? 2 : 1}
                  />
                  <text
                    x={node.x}
                    y={node.y + r + 14}
                    textAnchor="middle"
                    fontSize={11}
                    fill={isWeakBranch ? '#e2e8f0' : '#94a3b8'}
                  >
                    {node.title}
                  </text>
                </g>
              </Link>
            );
          })}
        </svg>
      </div>
      <p className="mt-3 text-xs text-slate-500">
        Tap any planet to drill that topic. The dashed ring marks today&apos;s
        recommended node; brighter planets are on the branch matching your
        current weakness.
      </p>
    </div>
  );
}
