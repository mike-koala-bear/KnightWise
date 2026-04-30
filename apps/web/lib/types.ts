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

export type DailyProgressOut = {
  date: string;
  solved: number;
  attempts: number;
  target: number;
  complete: boolean;
};

export type StreakOut = {
  current: number;
  longest: number;
  last_active: string | null;
};

export type SyncStartedResponse = {
  job_id: string;
  status: 'pending' | 'running' | 'done' | 'error';
};

export type SyncStatusResponse = {
  job_id: string;
  status: 'pending' | 'running' | 'done' | 'error';
  message: string;
  lichess_fetched: number;
  lichess_inserted: number;
  chesscom_fetched: number;
  chesscom_inserted: number;
  games_analyzed: number;
  games_failed: number;
  total_games_to_analyze: number;
  total_fetched: number;
  total_inserted: number;
  error: string | null;
  started_at: string;
  finished_at: string | null;
};

export type LLMHealth = {
  model: string;
  live: boolean;
  reason: string;
};

export type OnboardingState = {
  user_id: number;
  rating_mu: number;
  rating_sigma: number;
  attempts_so_far: number;
  completed_at: string | null;
  min_attempts: number;
  max_attempts: number;
};

export type OnboardingPuzzleOut = {
  id: number;
  external_id: string | null;
  fen: string;
  rating: number;
  description: string | null;
};

export type OnboardingNextOut = {
  done: boolean;
  puzzle: OnboardingPuzzleOut | null;
  state: OnboardingState;
};

export type OnboardingAttemptOut = {
  correct: boolean;
  expected_uci: string;
  state: OnboardingState;
  done: boolean;
};

export type OnboardingSetupOut = {
  user_id: number;
  lichess_username: string | null;
  chesscom_username: string | null;
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
