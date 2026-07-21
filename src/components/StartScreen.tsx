import { useState } from 'react';
import type { UserProfile, GameSettings } from '@/types';
import { createDefaultProfile } from '@/lib/achievements';
import { totalAvailable } from '@/lib/questionPool';
import { audio } from '@/lib/audio';

interface StartScreenProps {
  profile: UserProfile | null;
  settings: GameSettings;
  onStart: (profile: UserProfile) => void;
  onShowStats: () => void;
  onUpdateSettings: (s: GameSettings) => void;
}

const AVATARS = ['🦅', '🐺', '🦁', '🦊', '🐯', '🐉', '🦅', '⚡'];

export function StartScreen({ profile, settings, onStart, onShowStats, onUpdateSettings }: StartScreenProps) {
  const [username, setUsername] = useState(profile?.username ?? '');
  const [avatar, setAvatar] = useState(profile?.avatar ?? '🦅');
  const poolSize = totalAvailable(new Set());

  function start() {
    const name = username.trim() || 'Yarışmacı';
    audio.setEnabled(settings.soundEnabled);
    audio.setVolume(settings.volume);
    audio.resume();
    audio.play('jackpot');
    const p = profile ?? createDefaultProfile(name, avatar);
    p.username = name;
    p.avatar = avatar;
    onStart(p);
  }

  function toggleSound() {
    const next = { ...settings, soundEnabled: !settings.soundEnabled };
    onUpdateSettings(next);
    audio.setEnabled(next.soundEnabled);
    if (next.soundEnabled) audio.play('button');
  }

  function setVolume(v: number) {
    const next = { ...settings, volume: v };
    onUpdateSettings(next);
    audio.setVolume(v);
  }

  return (
    <div className="relative min-h-screen w-full overflow-hidden game-bg flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-gradient-to-b from-night-900/70 via-night-800/60 to-night-900/80" />
      {/* Floating orbs */}
      <div className="absolute top-10 left-10 w-72 h-72 rounded-full bg-cyan-500/10 blur-3xl animate-float-slow" />
      <div className="absolute bottom-10 right-10 w-96 h-96 rounded-full bg-amber-500/10 blur-3xl animate-float-slower" />

      <div className="relative z-10 w-full max-w-md">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-20 h-20 rounded-3xl bg-gradient-to-br from-amber-400 to-amber-600 shadow-gold-glow mb-4 animate-pulse-slow">
            <i className="fa-solid fa-crown text-4xl text-night-900" />
          </div>
          <h1 className="text-4xl lg:text-5xl font-black text-transparent bg-clip-text bg-gradient-to-r from-amber-200 via-amber-400 to-amber-200 mb-2 tracking-tight">
            KİM MİLYONER
          </h1>
          <p className="text-cyan-300/80 text-sm tracking-[0.3em] uppercase">OLMAK İSTER?</p>
          <p className="text-white/40 text-xs mt-3">Türkiye Bilgi Yarışması · Sonsuz Soru</p>
        </div>

        <div className="glass-panel rounded-3xl p-6 space-y-5">
          <div>
            <label className="block text-xs uppercase tracking-widest text-white/60 mb-2">Kullanıcı Adı</label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value.slice(0, 20))}
              placeholder="Adınızı girin"
              className="w-full rounded-xl bg-white/5 border border-white/15 px-4 py-3 text-white placeholder-white/30 focus:outline-none focus:border-cyan-400/60 focus:bg-white/10 transition"
            />
          </div>

          <div>
            <label className="block text-xs uppercase tracking-widest text-white/60 mb-2">Avatar</label>
            <div className="grid grid-cols-8 gap-2">
              {AVATARS.map((a, i) => (
                <button
                  key={i}
                  type="button"
                  onClick={() => setAvatar(a)}
                  className={`aspect-square rounded-lg text-xl flex items-center justify-center transition-all ${
                    avatar === a
                      ? 'bg-amber-400/30 border-2 border-amber-400 scale-110'
                      : 'bg-white/5 border border-white/10 hover:bg-white/10'
                  }`}
                >
                  {a}
                </button>
              ))}
            </div>
          </div>

          <div className="flex items-center justify-between gap-3">
            <button
              type="button"
              onClick={toggleSound}
              className="flex items-center gap-2 px-3 py-2 rounded-xl border border-white/15 bg-white/5 hover:bg-white/10 text-white/80 text-sm transition"
            >
              <i className={`fa-solid ${settings.soundEnabled ? 'fa-volume-high' : 'fa-volume-xmark'} text-cyan-300`} />
              {settings.soundEnabled ? 'Ses Açık' : 'Sesli Değil'}
            </button>
            <input
              type="range"
              min={0}
              max={1}
              step={0.05}
              value={settings.volume}
              onChange={(e) => setVolume(parseFloat(e.target.value))}
              className="flex-1 accent-cyan-400"
              aria-label="Ses seviyesi"
            />
          </div>

          <button
            type="button"
            onClick={start}
            className="w-full py-4 rounded-2xl bg-gradient-to-r from-amber-400 via-amber-500 to-amber-600 text-night-900 font-black text-lg tracking-wide hover:scale-[1.02] active:scale-95 transition-all shadow-gold-glow"
          >
            <i className="fa-solid fa-play mr-2" /> BAŞLA
          </button>

          {profile && (
            <button
              type="button"
              onClick={onShowStats}
              className="w-full py-3 rounded-2xl border border-cyan-400/30 bg-cyan-500/10 text-cyan-200 font-semibold hover:bg-cyan-500/20 transition"
            >
              <i className="fa-solid fa-chart-line mr-2" /> İstatistiklerim
            </button>
          )}

          <div className="text-center text-xs text-white/40">
            Soru havuzu: <span className="text-cyan-300 font-semibold">{poolSize}</span> soru
          </div>
        </div>
      </div>
    </div>
  );
}
