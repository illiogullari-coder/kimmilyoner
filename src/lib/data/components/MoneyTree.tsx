import type { MoneyLevel } from '@/types';

interface MoneyTreeProps {
  levels: MoneyLevel[];
  currentIndex: number;
  lost?: boolean;
}

export function MoneyTree({ levels, currentIndex, lost }: MoneyTreeProps) {
  const visible = levels.slice(Math.max(0, currentIndex - 3), currentIndex + 8);
  const startIndex = visible.length > 0 ? visible[0].index : 0;

  return (
    <div className="w-full max-w-[260px] flex flex-col gap-1.5 max-h-[70vh] overflow-y-auto pr-1 scrollbar-thin">
      {visible.map((level, i) => {
        const realIndex = startIndex + i;
        const isActive = realIndex === currentIndex;
        const isPassed = realIndex < currentIndex;
        const stateClass = lost && isActive
          ? 'border-red-500/70 bg-red-500/20 text-red-200 shadow-red-glow'
          : isActive
            ? 'border-amber-400/80 bg-amber-400/20 text-amber-200 shadow-gold-glow scale-[1.03]'
            : isPassed
              ? 'border-emerald-400/40 bg-emerald-400/10 text-emerald-200/80'
              : 'border-white/10 bg-white/5 text-white/60';
        return (
          <div
            key={level.index}
            className={`flex items-center justify-between rounded-lg border px-3 py-1.5 text-sm backdrop-blur-md transition-all duration-300 ${stateClass}`}
          >
            <span className="font-mono text-xs w-6 text-right opacity-70">{level.index + 1}</span>
            <span className="font-semibold tabular-nums flex-1 text-center">
              {level.amount.toLocaleString('tr-TR')} ₺
            </span>
            {level.isSafe && <span className="text-[10px] text-emerald-300/80">◆</span>}
          </div>
        );
      })}
    </div>
  );
}
