import type { AudienceVote } from '@/types';

interface AudienceChartProps {
  votes: AudienceVote[];
  eliminated: number[];
  correctIndex: number;
  revealed: boolean;
}

export function AudienceChart({ votes, eliminated, correctIndex, revealed }: AudienceChartProps) {
  const letters = ['A', 'B', 'C', 'D'];
  return (
    <div className="flex items-end justify-around h-40 gap-3 px-4 py-3 rounded-2xl bg-white/5 border border-white/10 backdrop-blur-md">
      {votes.map((v) => {
        const isEliminated = eliminated.includes(v.optionIndex);
        const height = isEliminated ? 0 : Math.max(2, v.percent);
        const showCorrect = revealed && v.optionIndex === correctIndex;
        return (
          <div key={v.optionIndex} className="flex flex-col items-center gap-1 flex-1 h-full justify-end">
            <span className={`text-xs font-bold ${showCorrect ? 'text-emerald-300' : 'text-white/80'}`}>
              {isEliminated ? '—' : `%${v.percent}`}
            </span>
            <div
              className={`w-full rounded-t-md transition-all duration-700 ease-out
                ${isEliminated ? 'bg-white/5' : showCorrect ? 'bg-gradient-to-t from-emerald-500 to-emerald-300' : 'bg-gradient-to-t from-fuchsia-600 to-fuchsia-400'}`}
              style={{ height: `${height}%` }}
            />
            <span className="text-xs font-mono text-white/60">{letters[v.optionIndex]}</span>
          </div>
        );
      })}
    </div>
  );
}
