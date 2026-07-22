import type {
  GameSaveState,
  GameSettings,
  UserProfile,
} from '@/types';
import { idbSet, idbGet, idbDelete } from '@/lib/idb';
import { ACHIEVEMENTS } from '@/lib/achievements';

const KEYS = {
  profile: 'kim.profile',
  settings: 'kim.settings',
  save: 'kim.save',
  seen: 'kim.seen',
} as const;

const BIGINT_MARKER = '__bigint__';

/** JSON, BigInt'i doğal desteklemez; işaretli bir sarmalayıcı ile serileştiriyoruz. */
function replacer(_key: string, value: unknown): unknown {
  if (typeof value === 'bigint') return { [BIGINT_MARKER]: value.toString() };
  return value;
}

function reviver(_key: string, value: unknown): unknown {
  if (value && typeof value === 'object' && BIGINT_MARKER in (value as Record<string, unknown>)) {
    return BigInt((value as Record<string, string>)[BIGINT_MARKER]);
  }
  return value;
}

function safeParse<T>(raw: string | null, fallback: T): T {
  if (!raw) return fallback;
  try {
    return JSON.parse(raw, reviver) as T;
  } catch {
    return fallback;
  }
}

function persist(key: string, value: unknown): void {
  const raw = JSON.stringify(value, replacer);
  localStorage.setItem(key, raw);
  // IndexedDB'ye asenkron ayna yazımı — sayfa akışını bloklamaz, hata olursa yutulur.
  void idbSet(key, raw);
}

/**
 * Eski (avatar/number tabanlı) profil kayıtlarını yeni (gender/BigInt tabanlı)
 * şemaya taşır. Geriye dönük uyumluluk için: mevcut kullanıcılar profillerini
 * kaybetmez, eksik alanlar güvenli varsayılanlarla tamamlanır.
 */
function migrateProfile(raw: unknown): UserProfile | null {
  if (!raw || typeof raw !== 'object') return null;
  const p = raw as Record<string, unknown>;
  const stats = (p.stats as Record<string, unknown>) ?? {};
  const toBigInt = (v: unknown): bigint => (typeof v === 'bigint' ? v : BigInt(Math.trunc(Number(v) || 0)));

  return {
    username: typeof p.username === 'string' ? p.username : 'Yarışmacı',
    gender: p.gender === 'kadın' ? 'kadın' : 'erkek',
    level: typeof p.level === 'number' ? p.level : 1,
    xp: typeof p.xp === 'number' ? p.xp : 0,
    createdAt: typeof p.createdAt === 'number' ? p.createdAt : Date.now(),
    stats: {
      totalGames: Number(stats.totalGames ?? 0),
      totalCorrect: Number(stats.totalCorrect ?? 0),
      totalWrong: Number(stats.totalWrong ?? 0),
      highestPrize: toBigInt(stats.highestPrize),
      totalPrize: toBigInt(stats.totalPrize),
      bestStreak: Number(stats.bestStreak ?? 0),
      fastestAnswerMs: Number(stats.fastestAnswerMs ?? 0),
      totalAnswerTimeMs: Number(stats.totalAnswerTimeMs ?? 0),
      totalAnswers: Number(stats.totalAnswers ?? 0),
      categoryStats: (stats.categoryStats as UserProfile['stats']['categoryStats']) ?? {},
      jokersUsed: {
        double: Number((stats.jokersUsed as Record<string, number>)?.double ?? 0),
        audience: Number((stats.jokersUsed as Record<string, number>)?.audience ?? 0),
        skip: Number((stats.jokersUsed as Record<string, number>)?.skip ?? 0),
        extraTime: Number((stats.jokersUsed as Record<string, number>)?.extraTime ?? 0),
      },
    },
    achievements: mergeAchievements(Array.isArray(p.achievements) ? (p.achievements as UserProfile['achievements']) : []),
  };
}

/** Eski profillerde bulunmayan yeni başarım tanımlarını (ör. joker_refresh) ekler. */
function mergeAchievements(existing: UserProfile['achievements']): UserProfile['achievements'] {
  const byId = new Map(existing.map((a) => [a.id, a]));
  return ACHIEVEMENTS.map((def) => byId.get(def.id) ?? { ...def });
}

export function loadProfile(): UserProfile | null {
  const raw = safeParse<unknown>(localStorage.getItem(KEYS.profile), null);
  return migrateProfile(raw);
}

export function saveProfile(profile: UserProfile): void {
  persist(KEYS.profile, profile);
}

/** IndexedDB'den kurtarma: LocalStorage boşsa (örn. temizlenmiş ama IDB hayatta kalmışsa) devreye girer. */
export async function recoverProfileFromIdb(): Promise<UserProfile | null> {
  const raw = await idbGet<string>(KEYS.profile);
  return safeParse<UserProfile | null>(raw, null);
}

export function loadSettings(): GameSettings {
  return safeParse<GameSettings>(localStorage.getItem(KEYS.settings), {
    soundEnabled: true,
    volume: 0.7,
    theme: 'dark',
  });
}

export function saveSettings(settings: GameSettings): void {
  persist(KEYS.settings, settings);
}

export function loadSave(): GameSaveState | null {
  return safeParse<GameSaveState | null>(localStorage.getItem(KEYS.save), null);
}

export function saveGame(state: GameSaveState): void {
  persist(KEYS.save, state);
}

export function clearSave(): void {
  localStorage.removeItem(KEYS.save);
  void idbDelete(KEYS.save);
}

export function loadSeenHashes(): Set<string> {
  const arr = safeParse<string[]>(localStorage.getItem(KEYS.seen), []);
  return new Set(arr);
}

export function addSeenHashes(hashes: string[]): void {
  const existing = loadSeenHashes();
  hashes.forEach((h) => {
    if (h) existing.add(h);
  });
  const arr = Array.from(existing).slice(-50000);
  persist(KEYS.seen, arr);
}
