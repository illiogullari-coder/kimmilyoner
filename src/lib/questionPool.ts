import type { Question, AnswerOption } from '@/types';
import { questions as rawQuestions } from '@/data/questions';
import { loadSeenHashes } from '@/lib/storage';

let pool: Question[] = [];
let seenHashes = loadSeenHashes();

export function getPool(): Question[] {
  if (pool.length === 0) {
    pool = [...rawQuestions];
  }
  return pool;
}

export function refreshSeenHashes(): void {
  seenHashes = loadSeenHashes();
}

export function shuffle<T>(arr: T[]): T[] {
  const a = [...arr];
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [a[i], a[j]] = [a[j], a[i]];
  }
  return a;
}

export function buildOptions(q: Question): AnswerOption[] {
  const opts: AnswerOption[] = [
    { text: q.correctAnswer, isCorrect: true },
    { text: q.distractors[0], isCorrect: false },
    { text: q.distractors[1], isCorrect: false },
    { text: q.distractors[2], isCorrect: false },
  ];
  return shuffle(opts);
}

export function pickNextQuestion(exclude: Set<string>): Question | null {
  const fullPool = getPool();
  const available = fullPool.filter((q) => !exclude.has(q.hash) && !seenHashes.has(q.hash));
  const list = available.length > 0 ? available : fullPool.filter((q) => !exclude.has(q.hash));
  if (list.length === 0) return null;
  return shuffle(list)[0];
}

export function pickQuestionsForLevel(count: number, exclude: Set<string>): Question[] {
  const fullPool = getPool();
  const available = fullPool.filter((q) => !exclude.has(q.hash) && !seenHashes.has(q.hash));
  const list = available.length > 0 ? available : fullPool.filter((q) => !exclude.has(q.hash));
  const shuffled = shuffle(list);
  const result: Question[] = [];
  const used = new Set<string>();
  for (const q of shuffled) {
    if (result.length >= count) break;
    if (used.has(q.hash)) continue;
    used.add(q.hash);
    result.push(q);
  }
  return result;
}

export function totalAvailable(exclude: Set<string>): number {
  const fullPool = getPool();
  const available = fullPool.filter((q) => !exclude.has(q.hash) && !seenHashes.has(q.hash));
  return available.length > 0 ? available.length : fullPool.filter((q) => !exclude.has(q.hash)).length;
}
