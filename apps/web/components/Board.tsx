'use client';

import { Chessboard } from 'react-chessboard';

type Props = {
  fen: string;
  orientation?: 'white' | 'black';
  onMove?: (from: string, to: string) => boolean | void;
  id?: string;
};

export function Board({ fen, orientation = 'white', onMove, id = 'knightwise-board' }: Props) {
  const options: Parameters<typeof Chessboard>[0]['options'] = {
    position: fen,
    id,
    boardOrientation: orientation,
  };
  if (onMove) {
    options.onPieceDrop = ({ sourceSquare, targetSquare }) => {
      if (!targetSquare) return false;
      const accepted = onMove(sourceSquare, targetSquare);
      return accepted !== false;
    };
  }
  return (
    <div className="overflow-hidden rounded-2xl ring-1 ring-white/10">
      <Chessboard options={options} />
    </div>
  );
}
