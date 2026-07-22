import { useEffect, useRef } from 'react';
import { getMoneyLevels } from '@/lib/moneyTree';

interface MoneyTreeProps {
  currentIndex: number;
  lost?: boolean;
}

const WINDOW_BEFORE = 3;
const WINDOW_AFTER = 8;

/**
 * Sonsuz para ağacı: sadece aktif seviyenin etrafındaki pencere hesaplanır
 * (BigInt ile sınırsız üretim, sabit boyutlu DOM). Kendi alanında sticky
 * kalır ve aktif satır otomatik olarak ortalanacak şekilde smooth scroll yapar.
 */
export function MoneyTree({ currentIndex, lost }: MoneyTreeProps) {
  const levels = getMoneyLevels(Math.max(0, currentIndex - WINDOW_BEFORE), currentIndex + WINDOW_AFTER);
  const activeRef = useRef<HTMLDivElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    activeRef.current?.scrollIntoView({ behavior: 'smooth', block: 'center' });
  }, [currentIndex]);

  return (
    <div
      ref={containerRef}
      className="sticky top-2 w-full max-w-[260px] flex flex-col gap-1.5 max-h-[70vh] overflow-y-auto pr-1 scrollbar-thin overscroll-contain"
    >
      {levels.map((level) => {
        const isActive = level.index === currentIndex;
        const isPassed = level.index < currentIndex;
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
            ref={isActive ? activeRef : undefined}
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
