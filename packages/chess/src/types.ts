export type Color = 'white' | 'black';

export type Move = {
  from: string;
  to: string;
  promotion?: 'q' | 'r' | 'b' | 'n';
  san?: string;
};

export type EvalCp = { kind: 'cp'; value: number };
export type EvalMate = { kind: 'mate'; value: number };
export type Eval = EvalCp | EvalMate;

export type WeaknessTag =
  | 'hanging_piece'
  | 'missed_fork'
  | 'missed_pin'
  | 'missed_skewer'
  | 'back_rank'
  | 'weak_king_safety'
  | 'bad_trade'
  | 'time_trouble'
  | 'endgame_technique'
  | 'opening_out_of_book';

export type AnalyzeResponse = {
  fen: string;
  depth: number;
  eval: Eval;
  bestMove: string;
};
