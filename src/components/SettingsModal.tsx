import { useState } from 'react';
import type { UserProfile } from '@/types';

interface SettingsModalProps {
  profile: UserProfile;
  onClose: () => void;
  onSave: (username: string) => void;
}

/**
 * Kullanıcı adı yalnızca ilk açılışta oluşturulur ve daha sonra yalnızca
 * buradan (Ayarlar) değiştirilebilir; ana ekrandan silinemez/boş bırakılamaz.
 */
export function SettingsModal({ profile, onClose, onSave }: SettingsModalProps) {
  const [username, setUsername] = useState(profile.username);
  const trimmed = username.trim();
  const valid = trimmed.length >= 2;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-night-900/80 backdrop-blur-md p-4">
      <div className="glass-panel rounded-3xl p-6 max-w-sm w-full animate-pop">
        <div className="flex items-center justify-between mb-5">
          <h2 className="font-display text-lg font-bold text-white">Ayarlar</h2>
          <button
            type="button"
            onClick={onClose}
            className="w-9 h-9 rounded-lg border border-white/15 bg-white/5 hover:bg-white/10 text-white/70 flex items-center justify-center"
            aria-label="Kapat"
          >
            <i className="fa-solid fa-xmark" />
          </button>
        </div>

        <label className="block text-xs uppercase tracking-widest text-white/60 mb-2">Kullanıcı Adı</label>
        <input
          type="text"
          value={username}
          onChange={(e) => setUsername(e.target.value.slice(0, 20))}
          className="w-full rounded-xl bg-white/5 border border-white/15 px-4 py-3 text-white placeholder-white/30 focus:outline-none focus:border-cyan-400/60 focus:bg-white/10 transition mb-5"
        />

        <button
          type="button"
          disabled={!valid}
          onClick={() => onSave(trimmed)}
          className="btn-sheen w-full py-3 rounded-2xl bg-gradient-to-r from-amber-400 via-amber-500 to-amber-600 text-night-900 font-bold hover:scale-[1.02] active:scale-95 transition-all shadow-gold-glow disabled:opacity-40 disabled:cursor-not-allowed disabled:hover:scale-100"
        >
          Kaydet
        </button>
      </div>
    </div>
  );
}
