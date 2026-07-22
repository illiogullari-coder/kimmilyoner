import { useEffect, useState } from 'react';
import type { GameSaveState, GameSettings, UserProfile } from '@/types';
import {
  loadProfile,
  saveProfile,
  loadSettings,
  saveSettings,
  loadSave,
  clearSave,
} from '@/lib/storage';
import { audio } from '@/lib/audio';
import { createDefaultProfile } from '@/lib/achievements';
import { StartScreen } from '@/components/StartScreen';
import { GameScreen } from '@/components/GameScreen';
import { StatsPanel } from '@/components/StatsPanel';

type Screen = 'start' | 'game' | 'stats';

export default function App() {
  const [screen, setScreen] = useState<Screen>('start');
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [settings, setSettings] = useState<GameSettings>({ soundEnabled: true, volume: 0.7, theme: 'dark' });
  const [save, setSave] = useState<GameSaveState | null>(null);

  useEffect(() => {
    const p = loadProfile();
    if (p) setProfile(p);
    setSettings(loadSettings());
    setSave(loadSave());
  }, []);

  function startGame(p: UserProfile) {
    setProfile(p);
    saveProfile(p);
    setSave(loadSave());
    setScreen('game');
  }

  function exitGame(updated: UserProfile) {
    setProfile(updated);
    saveProfile(updated);
    setSave(null);
    setScreen('start');
  }

  function updateSettings(s: GameSettings) {
    setSettings(s);
    saveSettings(s);
    audio.setEnabled(s.soundEnabled);
    audio.setVolume(s.volume);
  }

  function updateUsername(username: string) {
    if (!profile) return;
    const updated = { ...profile, username };
    setProfile(updated);
    saveProfile(updated);
  }

  function resetStats() {
    if (!profile) return;
    const fresh = createDefaultProfile(profile.username, profile.gender);
    setProfile(fresh);
    saveProfile(fresh);
    clearSave();
  }

  if (screen === 'game' && profile) {
    return (
      <GameScreen
        profile={profile}
        settings={settings}
        initialSave={save}
        onExit={exitGame}
      />
    );
  }

  return (
    <>
      <StartScreen
        profile={profile}
        settings={settings}
        onStart={startGame}
        onShowStats={() => setScreen('stats')}
        onUpdateSettings={updateSettings}
        onUpdateUsername={updateUsername}
      />
      {screen === 'stats' && profile && (
        <StatsPanel
          profile={profile}
          onClose={() => setScreen('start')}
          onReset={resetStats}
        />
      )}
    </>
  );
}
