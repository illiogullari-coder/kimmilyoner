import type { MoneyLevel } from '@/types';

const BASE_PRIZE = 10000000;
const SAFE_HAVEN_INTERVAL = 5;

export function buildMoneyTree(count: number): MoneyLevel[] {
  const levels: MoneyLevel[] = [];
  let current = BASE_PRIZE;
  for (let i = 0; i < count; i++) {
    const isSafe = i > 0 && i % SAFE_HAVEN_INTERVAL === 0;
    const isFinal = i === count - 1;
    levels.push({
      index: i,
      amount: current,
      isSafe,
      isFinal,
    });
    const growth = i < 5 ? 1.5 : i < 10 ? 1.4 : i < 20 ? 1.3 : 1.25;
    current = Math.round((current * growth) / 1000) * 1000;
  }
  return levels;
}

export function getSafeHavenAmount(levels: MoneyLevel[], currentIndex: number): number {
  let safe = 0;
  for (let i = Math.min(currentIndex, levels.length - 1); i >= 0; i--) {
    if (levels[i].isSafe) {
      safe = levels[i].amount;
      break;
    }
  }
  return safe;
}
