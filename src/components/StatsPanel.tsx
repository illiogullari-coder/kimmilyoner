import type { UserProfile } from '@/types';

interface StatsPanelProps {
  profile: UserProfile;
  onClose: () => void;
  onReset: () => void;
}

export function StatsPanel({ profile, onClose, onReset }: StatsPanelProps) {
  const s = profile.stats;
  const avgMs = s.totalAnswers > 0 ? Math.round(s.totalAnswerTimeMs / s.totalAnswers) : 0;
  const accuracy = s.totalAnswers > 0 ? Math.round((s.totalCorrect / s.totalAnswers) * 100) : 0;

  const statCards = [
    { label: 'Oynanan Oyun', value: s.totalGames, icon: 'fa-gamepad', color: 'text-cyan-300' },
    { label: 'Doğru Cevap', value: s.totalCorrect, icon: 'fa-check', color: 'text-emerald-300' },
    { label: 'Yanlış Cevap', value: s.totalWrong, icon: 'fa-xmark', color: 'text-red-300' },
    { label: 'Başarı Oranı', value: `%${accuracy}`, icon: 'fa-percent', color: 'text-amber-300' },
    { label: 'En Yüksek Ödül', value: `${s.highestPrize.toLocaleString('tr-TR')} ₺`, icon: 'fa-crown', color: 'text-amber-300' },
    { label: 'Toplam Kazanç', value: `${s.totalPrize.toLocaleString('tr-TR')} ₺`, icon: 'fa-money-bill-wave', color: 'text-emerald-300' },
    { label: 'En Uzun Seri', value: s.bestStreak, icon: 'fa-fire', color: 'text-orange-300' },
    { label: 'En Hızlı Cevap', value: s.fastestAnswerMs > 0 ? `${(s.fastestAnswerMs / 1000).toFixed(1)}s` : '—', icon: 'fa-stopwatch', color: 'text-cyan-300' },
    { label: 'Ort. Cevap Süresi', value: avgMs > 0 ? `${(avgMs / 1000).toFixed(1)}s` : '—', icon: 'fa-clock', color: 'text-cyan-300' },
  ];

  const topCategories = Object.entries(s.categoryStats)
    .map(([cat, c]) => ({ cat, total: c.correct + c.wrong, correct: c.correct }))
    .sort((a, b) => b.correct - a.correct)
    .slice(0, 6);

  return (
    <div className="fixed inset-0 z-40 flex items-center justify-center bg-night-900/80 backdrop-blur-md p-4 overflow-y-auto">
      <div className="glass-panel rounded-3xl p-6 max-w-2xl w-full my-8 animate-pop">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-full bg-gradient-to-br from-amber-400 to-amber-600 flex items-center justify-center text-xl">
              {profile.avatar}
            </div>
            <div>
              <h2 className="text-xl font-bold text-white">{profile.username}</h2>
              <p className="text-xs text-cyan-300/70">Seviye {profile.level} · {profile.xp} XP</p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="w-9 h-9 rounded-lg border border-white/15 bg-white/5 hover:bg-white/10 text-white/70 flex items-center justify-center"
          >
            <i className="fa-solid fa-xmark" />
          </button>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-3 gap-3 mb-6">
          {statCards.map((c) => (
            <div key={c.label} className="rounded-xl border border-white/10 bg-white/5 p-3">
              <i className={`fa-solid ${c.icon} ${c.color} mb-1`} />
              <div className="text-lg font-bold text-white tabular-nums">{c.value}</div>
              <div className="text-[10px] uppercase tracking-wider text-white/50">{c.label}</div>
            </div>
          ))}
        </div>

        {topCategories.length > 0 && (
          <div className="mb-6">
            <h3 className="text-sm font-semibold text-white/80 mb-3">Kategori Başarıları</h3>
            <div className="space-y-2">
              {topCategories.map((c) => {
                const pct = c.total > 0 ? Math.round((c.correct / c.total) * 100) : 0;
                return (
                  <div key={c.cat} className="flex items-center gap-3">
                    <span className="text-xs text-white/70 w-32 truncate">{c.cat}</span>
                    <div className="flex-1 h-2 rounded-full bg-white/10 overflow-hidden">
                      <div className="h-full bg-gradient-to-r from-cyan-400 to-emerald-400" style={{ width: `${pct}%` }} />
                    </div>
                    <span className="text-xs text-white/60 w-12 text-right">{c.correct}/{c.total}</span>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        <div className="mb-6">
          <h3 className="text-sm font-semibold text-white/80 mb-3">Başarımlar</h3>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
            {profile.achievements.map((a) => (
              <div
                key={a.id}
                className={`rounded-xl border p-2.5 flex items-center gap-2 ${
                  a.unlocked
                    ? 'border-amber-400/40 bg-amber-400/10'
                    : 'border-white/10 bg-white/5 opacity-50'
                }`}
              >
                <i className={`fa-solid ${a.icon} ${a.unlocked ? 'text-amber-300' : 'text-white/40'}`} />
                <div className="min-w-0">
                  <div className="text-xs font-semibold text-white truncate">{a.title}</div>
                  <div className="text-[10px] text-white/50 truncate">{a.description}</div>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="flex gap-3">
          <button
            type="button"
            onClick={onClose}
            className="flex-1 py-3 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 text-white font-semibold hover:scale-[1.02] transition"
          >
            Geri Dön
          </button>
          <button
            type="button"
            onClick={onReset}
            className="px-4 py-3 rounded-xl border border-red-500/30 bg-red-500/10 text-red-300 hover:bg-red-500/20 transition"
            aria-label="İstatistikleri sıfırla"
          >
            <i className="fa-solid fa-trash" />
          </button>
        </div>
      </div>
    </div>
  );
}
