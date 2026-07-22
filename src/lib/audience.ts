import type { AudienceVote, Question } from '@/types';

export function generateAudienceVotes(
  question: Question,
  eliminated: number[],
  correctIndex: number,
): AudienceVote[] {
  const totalOptions = 4;
  const activeIndices = [0, 1, 2, 3].filter((i) => !eliminated.includes(i));
  const correctActive = !eliminated.includes(correctIndex);

  const weights: number[] = new Array(totalOptions).fill(0);
  activeIndices.forEach((i) => {
    if (i === correctIndex) {
      weights[i] = 0.45 + Math.random() * 0.25;
    } else {
      weights[i] = 0.1 + Math.random() * 0.2;
    }
  });

  if (!correctActive && activeIndices.length > 0) {
    const misleading = activeIndices[Math.floor(Math.random() * activeIndices.length)];
    weights[misleading] = 0.35 + Math.random() * 0.3;
  }

  const total = weights.reduce((a, b) => a + b, 0);
  const normalized = weights.map((w) => (total > 0 ? (w / total) * 100 : 0));
  const rounded = normalized.map((p) => Math.round(p));
  let diff = 100 - rounded.reduce((a, b) => a + b, 0);
  if (diff !== 0) {
    const idx = activeIndices[Math.floor(Math.random() * activeIndices.length)];
    rounded[idx] += diff;
  }

  return rounded.map((percent, optionIndex) => ({ optionIndex, percent }));
}
