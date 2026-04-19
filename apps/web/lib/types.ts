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
