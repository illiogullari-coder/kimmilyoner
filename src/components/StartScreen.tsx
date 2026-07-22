import { useState } from 'react';
import type { UserProfile, GameSettings, Gender } from '@/types';
import { createDefaultProfile } from '@/lib/achievements';
import { totalAvailable } from '@/lib/questionPool';
import { audio } from '@/lib/audio';
import { SettingsModal } from '@/components/SettingsModal';

interface StartScreenProps {
  profile: UserProfile | null;
  settings: GameSettings;
  onStart: (profile: UserProfile) => void;
  onShowStats: () => void;
  onUpdateSettings: (s: GameSettings) => void;
  onUpdateUsername: (username: string) => void;
}

export function StartScreen({ profile, settings, onStart, onShowStats, onUpdateSettings, onUpdateUsername }: StartScreenProps) {
  const isNewUser = !profile;
  const [username, setUsername] = useState('');
  const [gender, setGender] = useState<Gender | null>(null);
  const [showSettings, setShowSettings] = useState(false);
  const poolSize = totalAvailable(new Set());

  function start() {
    audio.setEnabled(settings.soundEnabled);
    audio.setVolume(settings.volume);
    audio.resume();
    audio.play('jackpot');

    if (profile) {
      onStart(profile);
      return;
    }

    const name = username.trim() || 'Yarışmacı';
    const g: Gender = gender ?? 'erkek';
    const p = createDefaultProfile(name, g);
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

  const canStart = isNewUser ? username.trim().length >= 2 && gender !== null : true;

  return (
    <div className="relative min-h-screen w-full overflow-hidden game-bg flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-gradient-to-b from-night-900/70 via-night-800/60 to-night-900/80" />
      <div className="absolute top-10 left-10 w-72 h-72 rounded-full bg-cyan-500/10 blur-3xl animate-float-slow" />
      <div className="absolute bottom-10 right-10 w-96 h-96 rounded-full bg-amber-500/10 blur-3xl animate-float-slower" />

      <div className="relative z-10 w-full max-w-md">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-20 h-20 rounded-3xl bg-gradient-to-br from-amber-400 to-amber-600 shadow-gold-glow mb-4 animate-pulse-slow">
            <i className="fa-solid fa-crown text-4xl text-night-900" />
          </div>
          <h1 className="font-display text-4xl lg:text-5xl font-black shimmer-text mb-2 tracking-tight">
            KİM MİLYONER
          </h1>
          <p className="text-cyan-300/80 text-sm tracking-[0.3em] uppercase">OLMAK İSTER?</p>
          <p className="text-white/40 text-xs mt-3">Türkiye Bilgi Yarışması · Sonsuz Soru</p>
        </div>

        <div className="glass-panel rounded-3xl p-6 space-y-5">
          {isNewUser ? (
            <>
              <div>
                <label className="block text-xs uppercase tracking-widest text-white/60 mb-2">Kullanıcı Adı</label>
                <input
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value.slice(0, 20))}
                  placeholder="Adınızı girin"
                  className="w-full rounded-xl bg-white/5 border border-white/15 px-4 py-3 text-white placeholder-white/30 focus:outline-none focus:border-cyan-400/60 focus:bg-white/10 transition"
                />
                <p className="text-[11px] text-white/35 mt-1.5">
                  Kullanıcı adı yalnızca şimdi belirlenir; sonra sadece Ayarlar&apos;dan değiştirilebilir.
                </p>
              </div>

              <div>
                <label className="block text-xs uppercase tracking-widest text-white/60 mb-2">Cinsiyet</label>
                <div className="grid grid-cols-2 gap-3">
                  <button
                    type="button"
                    onClick={() => setGender('erkek')}
                    aria-pressed={gender === 'erkek'}
                    className={`flex flex-col items-center justify-center gap-2 rounded-2xl border py-5 transition-all ${
                      gender === 'erkek'
                        ? 'bg-cyan-400/20 border-cyan-400 scale-105'
                        : 'bg-white/5 border-white/10 hover:bg-white/10'
                    }`}
                  >
                    <i className="fa-solid fa-mars text-3xl text-cyan-200" />
                    <span className="text-sm font-semibold text-white/90">Erkek</span>
                  </button>
                  <button
                    type="button"
                    onClick={() => setGender('kadın')}
                    aria-pressed={gender === 'kadın'}
                    className={`flex flex-col items-center justify-center gap-2 rounded-2xl border py-5 transition-all ${
                      gender === 'kadın'
                        ? 'bg-fuchsia-400/20 border-fuchsia-400 scale-105'
                        : 'bg-white/5 border-white/10 hover:bg-white/10'
                    }`}
                  >
                    <i className="fa-solid fa-venus text-3xl text-fuchsia-200" />
                    <span className="text-sm font-semibold text-white/90">Kadın</span>
                  </button>
                </div>
              </div>
            </>
          ) : (
            <div className="flex items-center justify-between rounded-xl border border-white/10 bg-white/5 px-4 py-3">
              <div className="flex items-center gap-3">
                <i className={`fa-solid ${profile.gender === 'kadın' ? 'fa-venus text-fuchsia-300' : 'fa-mars text-cyan-300'} text-xl`} />
                <span className="text-white font-semibold">{profile.username}</span>
              </div>
              <button
                type="button"
                onClick={() => setShowSettings(true)}
                className="w-9 h-9 rounded-lg border border-white/15 bg-white/5 hover:bg-white/10 text-white/70 flex items-center justify-center"
                aria-label="Ayarlar"
              >
                <i className="fa-solid fa-gear" />
              </button>
            </div>
          )}

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
            disabled={!canStart}
            className="btn-sheen w-full py-4 rounded-2xl bg-gradient-to-r from-amber-400 via-amber-500 to-amber-600 text-night-900 font-black text-lg tracking-wide hover:scale-[1.02] active:scale-95 transition-all shadow-gold-glow disabled:opacity-40 disabled:cursor-not-allowed disabled:hover:scale-100"
          >
            <i className="fa-solid fa-play mr-2" /> BAŞLA
          </button>

          {profile && (
            <>
              <button
                type="button"
                onClick={onShowStats}
                className="btn-sheen w-full py-3 rounded-2xl border border-cyan-400/30 bg-cyan-500/10 text-cyan-200 font-semibold hover:bg-cyan-500/20 transition"
              >
                <i className="fa-solid fa-chart-line mr-2" /> İstatistiklerim
              </button>
              <p className="text-center text-[11px] tracking-[0.2em] uppercase text-white/30 font-medium -mt-2">
                Game Developer: Hamdi Uludağ
              </p>
            </>
          )}

          <div className="text-center text-xs text-white/40">
            Soru havuzu: <span className="text-cyan-300 font-semibold">{poolSize}</span> soru
          </div>
        </div>
      </div>

      {showSettings && profile && (
        <SettingsModal
          profile={profile}
          onClose={() => setShowSettings(false)}
          onSave={(name) => {
            onUpdateUsername(name);
            setShowSettings(false);
          }}
        />
      )}
    </div>
  );
}
