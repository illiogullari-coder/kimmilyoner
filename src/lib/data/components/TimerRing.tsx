interface TimerRingProps {
  total: number;
  remaining: number;
  danger?: boolean;
}

export function TimerRing({ total, remaining, danger }: TimerRingProps) {
  const radius = 54;
  const circumference = 2 * Math.PI * radius;
  const progress = Math.max(0, remaining / total);
  const offset = circumference * (1 - progress);

  const color = danger ? '#ff3b3b' : '#27e0c8';
  const glow = danger ? 'drop-shadow(0 0 8px #ff3b3b)' : 'drop-shadow(0 0 6px #27e0c8)';

  return (
    <div className={`relative ${danger ? 'animate-shake' : ''}`}>
      <svg width="128" height="128" viewBox="0 0 128 128" style={{ filter: glow }}>
        <circle
          cx="64"
          cy="64"
          r={radius}
          fill="none"
          stroke="rgba(255,255,255,0.08)"
          strokeWidth="8"
        />
        <circle
          cx="64"
          cy="64"
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth="8"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          transform="rotate(-90 64 64)"
          style={{ transition: 'stroke-dashoffset 1s linear, stroke 0.3s' }}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span
          className={`text-3xl font-bold tabular-nums ${danger ? 'text-red-400 animate-pulse' : 'text-cyan-200'}`}
        >
          {Math.ceil(remaining)}
        </span>
        <span className="text-[10px] uppercase tracking-widest text-white/50">saniye</span>
      </div>
    </div>
  );
}
