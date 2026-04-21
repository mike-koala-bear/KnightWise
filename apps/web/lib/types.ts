export type PuzzleOut = {
  id: number;
  external_id: string | null;
  fen: string;
  solution_uci: string[];
  themes: string[];
  rating: number;
  description: string | null;
};

export type NodeOut = {
  id: number;
  slug: string;
  domain: string;
  title: string;
  description: string | null;
};

export type NextDrillOut = {
  puzzle: PuzzleOut | null;
  node: NodeOut | null;
};

export type AttemptResponse = {
  ease: number;
  interval_days: number;
  repetitions: number;
  due_at: string;
};

export type WarpPuzzle = {
  id: number;
  fen: string;
  solution_uci: string[];
  themes: string[];
  rating: number;
  description: string | null;
};

export type WarpTagCount = {
  tag: string;
  count: number;
};

export type DailyWarpOut = {
  user_id: number;
  generated_at: string;
  games_analyzed: number;
  top_weakness_tag: string | null;
  tag_counts: WarpTagCount[];
  node_id: number | null;
  node_slug: string | null;
  node_title: string | null;
  coach_note: string;
  drill_puzzles: WarpPuzzle[];
};

export type RatingPoint = {
  day: string;
  rating: number | null;
};

export type RatingHistoryOut = {
  user_id: number;
  days: number;
  points: RatingPoint[];
  current_rating: number | null;
  delta: number | null;
};

export type GalaxyNode = {
  id: number;
  slug: string;
  domain: string;
  title: string;
  description: string | null;
  rating_min: number;
  rating_max: number;
  branch_group: string | null;
  prereq_slugs: string[];
};
