'use client';

import { Chessboard } from 'react-chessboard';

type Props = {
  fen: string;
};

export function Board({ fen }: Props) {
  return (
    <div className="overflow-hidden rounded-2xl ring-1 ring-white/10">
      <Chessboard options={{ position: fen, id: 'knightwise-board' }} />
    </div>
  );
}
