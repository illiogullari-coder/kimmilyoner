import type { MoneyLevel } from '@/types';

const FIRST_PRIZE = 500n;
const SAFE_HAVEN_INTERVAL = 5;

/**
 * Sonsuz para ağacı: her seviye bir öncekinin iki katıdır (500, 1000, 2000, ...).
 * BigInt kullanıldığı için overflow olmadan sınırsız seviye üretilebilir.
 * Seviyeler dizi olarak önceden üretilmez; her seviye anlık hesaplanır.
 */
export function getMoneyLevel(index: number): MoneyLevel {
  const safeIndex = Math.max(0, Math.trunc(index));
  const amount = FIRST_PRIZE * 2n ** BigInt(safeIndex);
  const isSafe = safeIndex > 0 && safeIndex % SAFE_HAVEN_INTERVAL === 0;
  return { index: safeIndex, amount, isSafe };
}

/** [start, end] aralığındaki seviyeleri (dahil) döndürür — sonsuz ağacın görünür penceresi için kullanılır. */
export function getMoneyLevels(start: number, end: number): MoneyLevel[] {
  const from = Math.max(0, start);
  const to = Math.max(from, end);
  const levels: MoneyLevel[] = [];
  for (let i = from; i <= to; i++) levels.push(getMoneyLevel(i));
  return levels;
}

/** currentIndex'e kadar (dahil değil) geçilmiş en son güvenli liman tutarı. */
export function getSafeHavenAmount(currentIndex: number): bigint {
  const safeIndex = Math.floor(currentIndex / SAFE_HAVEN_INTERVAL) * SAFE_HAVEN_INTERVAL;
  if (safeIndex <= 0) return 0n;
  return getMoneyLevel(safeIndex).amount;
}

export function formatMoney(amount: bigint): string {
  return `${amount.toLocaleString('tr-TR')} ₺`;
}
