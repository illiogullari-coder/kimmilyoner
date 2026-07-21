import type {
  GameSaveState,
  GameSettings,
  UserProfile,
} from '@/types';

const KEYS = {
  profile: 'kim.profile',
  settings: 'kim.settings',
  save: 'kim.save',
  seen: 'kim.seen',
} as const;

function safeParse<T>(raw: string | null, fallback: T): T {
  if (!raw) return fallback;
  try {
    return JSON.parse(raw) as T;
  } catch {
    return fallback;
  }
}

export function loadProfile(): UserProfile | null {
  return safeParse<UserProfile | null>(localStorage.getItem(KEYS.profile), null);
}

export function saveProfile(profile: UserProfile): void {
  localStorage.setItem(KEYS.profile, JSON.stringify(profile));
}

export function loadSettings(): GameSettings {
  return safeParse<GameSettings>(localStorage.getItem(KEYS.settings), {
    soundEnabled: true,
    volume: 0.7,
    theme: 'dark',
  });
}

export function saveSettings(settings: GameSettings): void {
  localStorage.setItem(KEYS.settings, JSON.stringify(settings));
}

export function loadSave(): GameSaveState | null {
  return safeParse<GameSaveState | null>(localStorage.getItem(KEYS.save), null);
}

export function saveGame(state: GameSaveState): void {
  localStorage.setItem(KEYS.save, JSON.stringify(state));
}

export function clearSave(): void {
  localStorage.removeItem(KEYS.save);
}

export function loadSeenHashes(): Set<string> {
  const arr = safeParse<string[]>(localStorage.getItem(KEYS.seen), []);
  return new Set(arr);
}

export function addSeenHashes(hashes: string[]): void {
  const existing = loadSeenHashes();
  hashes.forEach((h) => existing.add(h));
  const arr = Array.from(existing).slice(-50000);
  localStorage.setItem(KEYS.seen, JSON.stringify(arr));
}
