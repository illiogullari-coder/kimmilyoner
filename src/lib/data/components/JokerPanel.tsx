import type { JokerState, JokerType } from '@/types';

interface JokerPanelProps {
  jokers: JokerState;
  onUse: (type: JokerType) => void;
  disabled: boolean;
}

const JOKER_META: Record<JokerType, { label: string; icon: string; color: string }> = {
  double: { label: 'Çift Cevap', icon: 'fa-clone', color: 'from-cyan-400 to-blue-500' },
  audience: { label: 'Seyirci', icon: 'fa-users', color: 'from-fuchsia-400 to-pink-500' },
  skip: { label: 'Soruyu Geç', icon: 'fa-forward', color: 'from-amber-400 to-orange-500' },
};

export function JokerPanel({ jokers, onUse, disabled }: JokerPanelProps) {
  const types: JokerType[] = ['double', 'audience', 'skip'];
  return (
    <div className="flex gap-3 justify-center">
      {types.map((t) => {
        const used = !jokers[t];
        const meta = JOKER_META[t];
        return (
          <button
            key={t}
            type="button"
            disabled={used || disabled}
            onClick={() => onUse(t)}
            aria-label={meta.label}
            className={`group relative flex flex-col items-center justify-center w-16 h-16 rounded-2xl border transition-all duration-300
              ${used
                ? 'border-white/10 bg-white/5 opacity-40 cursor-not-allowed'
                : 'border-white/20 bg-gradient-to-br ' + meta.color + ' hover:scale-110 hover:shadow-lg hover:shadow-cyan-500/30 cursor-pointer'}
            `}
          >
            <i className={`fa-solid ${meta.icon} text-xl ${used ? 'text-white/40' : 'text-white'}`} />
            <span className="text-[9px] mt-0.5 text-white/90 font-medium">{meta.label}</span>
            {used && (
              <span className="absolute inset-0 flex items-center justify-center">
                <i className="fa-solid fa-ban text-red-400/60 text-2xl" />
              </span>
            )}
          </button>
        );
      })}
    </div>
  );
}
