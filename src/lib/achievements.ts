import type { Achievement, Gender, JokerType, UserProfile } from '@/types';

export const ACHIEVEMENTS: Achievement[] = [
  { id: 'first_game', title: 'İlk Adım', description: 'İlk oyununu tamamla', icon: 'fa-flag', unlocked: false },
  { id: 'first_correct', title: 'İlk Doğru', description: 'İlk soruyu doğru yanıtla', icon: 'fa-check', unlocked: false },
  { id: 'streak_5', title: 'Seri 5', description: 'Üst üste 5 doğru cevap', icon: 'fa-fire', unlocked: false },
  { id: 'streak_10', title: 'Seri 10', description: 'Üst üste 10 doğru cevap', icon: 'fa-bolt', unlocked: false },
  { id: 'millionaire', title: 'Milyoner', description: '10.000.000 TL kazan', icon: 'fa-crown', unlocked: false },
  { id: 'fast_answer', title: 'Şimşek', description: '5 saniyeden kısa sürede doğru yanıtla', icon: 'fa-stopwatch', unlocked: false },
  { id: 'joker_master', title: 'Joker Ustası', description: 'Tüm jokerleri tek oyunda kullan', icon: 'fa-mask', unlocked: false },
  { id: 'category_master', title: 'Kategori Ustası', description: 'Bir kategoride 10 doğru', icon: 'fa-trophy', unlocked: false },
  { id: 'level_10', title: 'Seviye 10', description: 'Seviye 10\'a ulaş', icon: 'fa-star', unlocked: false },
  { id: 'games_50', title: 'Bağımlı', description: '50 oyun oyna', icon: 'fa-gamepad', unlocked: false },
  { id: 'joker_refresh', title: 'Yeniden Doğuş', description: 'Jokerlerin bir kez otomatik yenilensin', icon: 'fa-rotate', unlocked: false },
];

export function createDefaultProfile(username: string, gender: Gender): UserProfile {
  return {
    username,
    gender,
    level: 1,
    xp: 0,
    createdAt: Date.now(),
    stats: {
      totalGames: 0,
      totalCorrect: 0,
      totalWrong: 0,
      highestPrize: 0n,
      totalPrize: 0n,
      bestStreak: 0,
      fastestAnswerMs: 0,
      totalAnswerTimeMs: 0,
      totalAnswers: 0,
      categoryStats: {},
      jokersUsed: { double: 0, audience: 0, skip: 0, extraTime: 0 },
    },
    achievements: ACHIEVEMENTS.map((a) => ({ ...a })),
  };
}

export function xpForLevel(level: number): number {
  return level * 500;
}

export function addXp(profile: UserProfile, amount: number): { leveledUp: boolean; newLevel: number } {
  profile.xp += amount;
  let leveledUp = false;
  while (profile.xp >= xpForLevel(profile.level)) {
    profile.xp -= xpForLevel(profile.level);
    profile.level += 1;
    leveledUp = true;
  }
  return { leveledUp, newLevel: profile.level };
}

export function updateStats(
  profile: UserProfile,
  correct: boolean,
  category: string,
  answerTimeMs: number,
  prize: bigint,
  streak: number,
): void {
  const s = profile.stats;
  s.totalAnswers += 1;
  s.totalAnswerTimeMs += answerTimeMs;
  if (correct) {
    s.totalCorrect += 1;
    if (s.fastestAnswerMs === 0 || answerTimeMs < s.fastestAnswerMs) s.fastestAnswerMs = answerTimeMs;
    if (streak > s.bestStreak) s.bestStreak = streak;
  } else {
    s.totalWrong += 1;
  }
  if (category) {
    s.categoryStats[category] = s.categoryStats[category] || { correct: 0, wrong: 0 };
    if (correct) s.categoryStats[category].correct += 1;
    else s.categoryStats[category].wrong += 1;
  }
  if (prize > s.highestPrize) s.highestPrize = prize;
}

export function recordFinalPrize(profile: UserProfile, prize: bigint): void {
  profile.stats.totalPrize += prize;
  if (prize > profile.stats.highestPrize) profile.stats.highestPrize = prize;
}

export function recordJokerUsage(profile: UserProfile, type: JokerType): void {
  profile.stats.jokersUsed[type] = (profile.stats.jokersUsed[type] ?? 0) + 1;
}

export function checkAchievements(
  profile: UserProfile,
  context: { streak: number; prize: bigint; answerTimeMs: number; allJokersUsed: boolean; jokersRefreshed: boolean },
): Achievement[] {
  const newlyUnlocked: Achievement[] = [];
  const s = profile.stats;
  const unlock = (id: string): boolean => {
    const a = profile.achievements.find((x) => x.id === id);
    if (a && !a.unlocked) {
      a.unlocked = true;
      a.unlockedAt = Date.now();
      newlyUnlocked.push(a);
      return true;
    }
    return false;
  };

  if (s.totalGames >= 1) unlock('first_game');
  if (s.totalCorrect >= 1) unlock('first_correct');
  if (s.bestStreak >= 5) unlock('streak_5');
  if (s.bestStreak >= 10) unlock('streak_10');
  if (s.highestPrize >= 10000000n) unlock('millionaire');
  if (context.answerTimeMs > 0 && context.answerTimeMs < 5000 && s.totalCorrect > 0) unlock('fast_answer');
  if (context.allJokersUsed) unlock('joker_master');
  if (context.jokersRefreshed) unlock('joker_refresh');
  if (Object.values(s.categoryStats).some((c) => c.correct >= 10)) unlock('category_master');
  if (profile.level >= 10) unlock('level_10');
  if (s.totalGames >= 50) unlock('games_50');
  return newlyUnlocked;
}
