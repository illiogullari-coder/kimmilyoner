export type Difficulty =
  | 'Kolay'
  | 'Normal'
  | 'Orta'
  | 'Zor'
  | 'Çok Zor'
  | 'Uzman'
  | 'Profesör'
  | 'Akademisyen'
  | 'Final';

export interface Question {
  id: string;
  hash: string;
  category: string;
  difficulty: Difficulty;
  question: string;
  correctAnswer: string;
  distractors: [string, string, string];
  source?: string;
}

export interface AnswerOption {
  text: string;
  isCorrect: boolean;
}

export type JokerType = 'double' | 'audience' | 'skip' | 'extraTime';

export interface JokerState {
  double: boolean;
  audience: boolean;
  skip: boolean;
  extraTime: boolean;
}

export interface AudienceVote {
  optionIndex: number;
  percent: number;
}

export interface GameStats {
  totalGames: number;
  totalCorrect: number;
  totalWrong: number;
  highestPrize: bigint;
  totalPrize: bigint;
  bestStreak: number;
  fastestAnswerMs: number;
  totalAnswerTimeMs: number;
  totalAnswers: number;
  categoryStats: Record<string, { correct: number; wrong: number }>;
  jokersUsed: Record<JokerType, number>;
}

export interface Achievement {
  id: string;
  title: string;
  description: string;
  icon: string;
  unlocked: boolean;
  unlockedAt?: number;
}

/** Kullanıcı sadece ilk açılışta cinsiyet sembolü seçer; avatar resmi yoktur. */
export type Gender = 'erkek' | 'kadın';

export interface UserProfile {
  username: string;
  /** @deprecated Avatar sistemi kaldırıldı, geriye dönük uyumluluk için tutulur. */
  avatar?: string;
  gender: Gender;
  level: number;
  xp: number;
  stats: GameStats;
  achievements: Achievement[];
  createdAt: number;
}

export interface GameSettings {
  soundEnabled: boolean;
  volume: number;
  theme: 'dark' | 'light';
}

export interface GameSaveState {
  currentQuestionIndex: number;
  currentPrize: bigint;
  jokers: JokerState;
  usedQuestionHashes: string[];
  activeQuestion: Question | null;
  timeRemaining: number;
  doubleAnswerActive: boolean;
  doubleAnswerSelected: number[];
  eliminatedOptions: number[];
  audienceVotes: AudienceVote[] | null;
  status: 'playing' | 'won' | 'lost' | 'idle';
  streak: number;
  correctSinceJokerRefresh: number;
  lastCategory: string | null;
}

export interface MoneyLevel {
  index: number;
  amount: bigint;
  isSafe: boolean;
}
