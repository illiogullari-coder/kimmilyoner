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

export type JokerType = 'double' | 'audience' | 'skip';

export interface JokerState {
  double: boolean;
  audience: boolean;
  skip: boolean;
}

export interface AudienceVote {
  optionIndex: number;
  percent: number;
}

export interface GameStats {
  totalGames: number;
  totalCorrect: number;
  totalWrong: number;
  highestPrize: number;
  totalPrize: number;
  bestStreak: number;
  fastestAnswerMs: number;
  totalAnswerTimeMs: number;
  totalAnswers: number;
  categoryStats: Record<string, { correct: number; wrong: number }>;
}

export interface Achievement {
  id: string;
  title: string;
  description: string;
  icon: string;
  unlocked: boolean;
  unlockedAt?: number;
}

export interface UserProfile {
  username: string;
  avatar: string;
  level: number;
  xp: number;
  stats: GameStats;
  achievements: Achievement[];
}

export interface GameSettings {
  soundEnabled: boolean;
  volume: number;
  theme: 'dark' | 'light';
}

export interface GameSaveState {
  currentQuestionIndex: number;
  currentPrize: number;
  jokers: JokerState;
  usedQuestionHashes: string[];
  activeQuestion: Question | null;
  timeRemaining: number;
  doubleAnswerActive: boolean;
  doubleAnswerSelected: number[];
  eliminatedOptions: number[];
  audienceVotes: AudienceVote[] | null;
  status: 'playing' | 'won' | 'lost' | 'idle';
}

export interface MoneyLevel {
  index: number;
  amount: number;
  isSafe: boolean;
  isFinal: boolean;
}
