import { useEffect, useMemo, useRef, useState } from 'react';
import type {
  AnswerOption,
  GameSaveState,
  GameSettings,
  JokerState,
  JokerType,
  MoneyLevel,
  Question,
  UserProfile,
} from '@/types';
import { buildMoneyTree, getSafeHavenAmount } from '@/lib/moneyTree';
import { buildOptions, pickNextQuestion, shuffle } from '@/lib/questionPool';
import { generateAudienceVotes } from '@/lib/audience';
import { audio } from '@/lib/audio';
import { addSeenHashes, saveGame, clearSave, saveProfile } from '@/lib/storage';
import { addXp, checkAchievements, updateStats } from '@/lib/achievements';
import { TimerRing } from '@/components/TimerRing';
import { MoneyTree } from '@/components/MoneyTree';
import { JokerPanel } from '@/components/JokerPanel';
import { AudienceChart } from '@/components/AudienceChart';
import { Confetti } from '@/components/Confetti';

interface GameScreenProps {
  profile: UserProfile;
  settings: GameSettings;
  initialSave: GameSaveState | null;
  onExit: (updatedProfile: UserProfile) => void;
}

const QUESTION_TIME = 30;
const TOTAL_LEVELS = 15;

type Phase = 'asking' | 'revealing' | 'correct' | 'wrong' | 'won' | 'lost';

export function GameScreen({ profile, settings, initialSave, onExit }: GameScreenProps) {
  const tree = useMemo<MoneyLevel[]>(() => buildMoneyTree(TOTAL_LEVELS), []);

  const [question, setQuestion] = useState<Question | null>(null);
  const [options, setOptions] = useState<AnswerOption[]>([]);
  const [correctIndex, setCorrectIndex] = useState<number>(-1);
  const [levelIndex, setLevelIndex] = useState<number>(0);
  const [usedHashes, setUsedHashes] = useState<Set<string>>(new Set());
  const [timeLeft, setTimeLeft] = useState<number>(QUESTION_TIME);
  const [phase, setPhase] = useState<Phase>('asking');
  const [selected, setSelected] = useState<number[]>([]);
  const [locked, setLocked] = useState<boolean>(false);
  const [jokers, setJokers] = useState<JokerState>({ double: true, audience: true, skip: true });
  const [eliminated, setEliminated] = useState<number[]>([]);
  const [audienceVotes, setAudienceVotes] = useState<ReturnType<typeof generateAudienceVotes> | null>(null);
  const [doubleActive, setDoubleActive] = useState<boolean>(false);
  const [streak, setStreak] = useState<number>(0);
  const [showWin, setShowWin] = useState<boolean>(false);
  const [showLose, setShowLose] = useState<boolean>(false);
  const [achievementToast, setAchievementToast] = useState<string | null>(null);
  const [levelUpToast, setLevelUpToast] = useState<string | null>(null);
  const answerStartRef = useRef<number>(0);
  const intervalRef = useRef<number>(0);

  useEffect(() => {
    audio.setEnabled(settings.soundEnabled);
    audio.setVolume(settings.volume);
    audio.play('intro');
    return () => {
      if (intervalRef.current) window.clearInterval(intervalRef.current);
    };
  }, [settings.soundEnabled, settings.volume]);

  useEffect(() => {
    if (initialSave && initialSave.activeQuestion) {
      const s = initialSave;
      const restoredQ = s.activeQuestion;
      if (!restoredQ) return;
      setLevelIndex(s.currentQuestionIndex);
      setJokers(s.jokers);
      setUsedHashes(new Set(s.usedQuestionHashes));
      setQuestion(restoredQ);
      const restoredOpts = buildOptions(restoredQ);
      setOptions(restoredOpts);
      setCorrectIndex(restoredOpts.findIndex((o) => o.isCorrect));
      setTimeLeft(s.timeRemaining);
      setDoubleActive(s.doubleAnswerActive);
      setEliminated(s.eliminatedOptions);
      if (s.audienceVotes) setAudienceVotes(s.audienceVotes);
    } else {
      loadNextQuestion(0, new Set());
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function loadNextQuestion(level: number, exclude: Set<string>) {
    const q = pickNextQuestion(exclude);
    if (!q) return;
    const opts = buildOptions(q);
    const ci = opts.findIndex((o) => o.isCorrect);
    setQuestion(q);
    setOptions(opts);
    setCorrectIndex(ci);
    setLevelIndex(level);
    setUsedHashes((prev) => new Set([...prev, q.hash]));
    setTimeLeft(QUESTION_TIME);
    setPhase('asking');
    setSelected([]);
    setLocked(false);
    setEliminated([]);
    setAudienceVotes(null);
    setDoubleActive(false);
    answerStartRef.current = performance.now();
    startTimer();
    persistSave(level, q, QUESTION_TIME);
  }

  function startTimer() {
    if (intervalRef.current) window.clearInterval(intervalRef.current);
    intervalRef.current = window.setInterval(() => {
      setTimeLeft((t) => {
        if (t <= 1) {
          window.clearInterval(intervalRef.current);
          handleTimeout();
          return 0;
        }
        if (t <= 6) audio.play('timerFinal');
        else if (t <= 10) audio.play('timer');
        return t - 1;
      });
    }, 1000);
  }

  function persistSave(level: number, q: Question | null, time: number) {
    const state: GameSaveState = {
      currentQuestionIndex: level,
      currentPrize: tree[level]?.amount ?? 0,
      jokers: jokers,
      usedQuestionHashes: Array.from(usedHashes),
      activeQuestion: q,
      timeRemaining: time,
      doubleAnswerActive: doubleActive,
      doubleAnswerSelected: selected,
      eliminatedOptions: eliminated,
      audienceVotes: audienceVotes,
      status: 'playing',
    };
    saveGame(state);
  }

  function handleTimeout() {
    setLocked(true);
    setPhase('lost');
    setShowLose(true);
    audio.play('lose');
    finalizeGame(false, 0, true);
  }

  function selectOption(index: number) {
    if (locked || phase !== 'asking') return;
    if (eliminated.includes(index)) return;

    if (doubleActive) {
      const newSel = selected.includes(index)
        ? selected.filter((i) => i !== index)
        : [...selected, index];
      setSelected(newSel);
      if (newSel.length === 2) {
        audio.play('button');
        revealDoubleAnswer(newSel);
      } else {
        audio.play('button');
      }
      return;
    }

    setSelected([index]);
    setLocked(true);
    audio.play('button');
    revealAnswer(index);
  }

  function revealAnswer(index: number) {
    if (intervalRef.current) window.clearInterval(intervalRef.current);
    setPhase('revealing');
    const elapsed = performance.now() - answerStartRef.current;
    const isCorrect = options[index]?.isCorrect ?? false;

    setTimeout(() => {
      if (isCorrect) {
        setPhase('correct');
        audio.play('correct');
        const prize = tree[levelIndex]?.amount ?? 0;
        const newStreak = streak + 1;
        setStreak(newStreak);
        updateStats(profile, true, question?.category ?? '', elapsed, prize, newStreak);
        const xpResult = addXp(profile, 100 + levelIndex * 20);
        if (xpResult.leveledUp) {
          setLevelUpToast(`Seviye atladın: ${xpResult.newLevel}!`);
          setTimeout(() => setLevelUpToast(null), 3000);
        }
        const achievements = checkAchievements(profile, {
          streak: newStreak,
          prize,
          answerTimeMs: elapsed,
          allJokersUsed: !jokers.double && !jokers.audience && !jokers.skip,
        });
        if (achievements.length > 0) {
          setAchievementToast(`${achievements[0].title}: ${achievements[0].description}`);
          setTimeout(() => setAchievementToast(null), 3500);
        }
        saveProfile(profile);
        addSeenHashes([question?.hash ?? '']);

        setTimeout(() => {
          if (levelIndex + 1 >= TOTAL_LEVELS) {
            setPhase('won');
            setShowWin(true);
            audio.play('win');
            finalizeGame(true, prize, false);
          } else {
            if (tree[levelIndex]?.isSafe) audio.play('barrier');
            loadNextQuestion(levelIndex + 1, new Set([...usedHashes, question?.hash ?? '']));
          }
        }, 1800);
      } else {
        setPhase('wrong');
        audio.play('wrong');
        finalizeGame(false, getSafeHavenAmount(tree, levelIndex), false);
      }
    }, 800);
  }

  function revealDoubleAnswer(indices: number[]) {
    if (intervalRef.current) window.clearInterval(intervalRef.current);
    setLocked(true);
    setPhase('revealing');
    const elapsed = performance.now() - answerStartRef.current;
    const correctInSelection = indices.some((i) => options[i]?.isCorrect);

    setTimeout(() => {
      if (correctInSelection) {
        setPhase('correct');
        audio.play('correct');
        const prize = tree[levelIndex]?.amount ?? 0;
        const newStreak = streak + 1;
        setStreak(newStreak);
        updateStats(profile, true, question?.category ?? '', elapsed, prize, newStreak);
        addXp(profile, 100 + levelIndex * 20);
        saveProfile(profile);
        addSeenHashes([question?.hash ?? '']);
        setTimeout(() => {
          if (levelIndex + 1 >= TOTAL_LEVELS) {
            setPhase('won');
            setShowWin(true);
            audio.play('win');
            finalizeGame(true, prize, false);
          } else {
            loadNextQuestion(levelIndex + 1, new Set([...usedHashes, question?.hash ?? '']));
          }
        }, 1800);
      } else {
        setPhase('wrong');
        audio.play('wrong');
        finalizeGame(false, getSafeHavenAmount(tree, levelIndex), false);
      }
    }, 800);
  }

  function finalizeGame(won: boolean, prize: number, timeout: boolean) {
    profile.stats.totalGames += 1;
    if (prize > profile.stats.highestPrize) profile.stats.highestPrize = prize;
    profile.stats.totalPrize += prize;
    checkAchievements(profile, {
      streak,
      prize,
      answerTimeMs: 0,
      allJokersUsed: !jokers.double && !jokers.audience && !jokers.skip,
    });
    saveProfile(profile);
    addSeenHashes(Array.from(usedHashes));
    clearSave();
    void won; void timeout;
  }

  function useJoker(type: JokerType) {
    if (locked || phase !== 'asking') return;
    if (!jokers[type]) return;
    audio.play('joker');
    setJokers((j) => ({ ...j, [type]: false }));

    if (type === 'double') {
      setDoubleActive(true);
    } else if (type === 'audience') {
      if (question) {
        const votes = generateAudienceVotes(question, eliminated, correctIndex);
        setAudienceVotes(votes);
      }
    } else if (type === 'skip') {
      addSeenHashes([question?.hash ?? '']);
      const newExclude = new Set([...usedHashes, question?.hash ?? '']);
      loadNextQuestion(levelIndex, newExclude);
    }
  }

  function quitGame() {
    if (intervalRef.current) window.clearInterval(intervalRef.current);
    const prize = getSafeHavenAmount(tree, levelIndex);
    finalizeGame(false, prize, false);
    onExit(profile);
  }

  const letters = ['A', 'B', 'C', 'D'];
  const currentPrize = tree[levelIndex]?.amount ?? 0;

  return (
    <div className="relative min-h-screen w-full overflow-hidden game-bg">
      <div className="absolute inset-0 bg-gradient-to-b from-night-900/80 via-night-800/70 to-night-900/90" />
      <div className="relative z-10 min-h-screen flex flex-col lg:flex-row gap-4 p-4 lg:p-6 max-w-[1400px] mx-auto">
        {/* Money tree sidebar */}
        <aside className="lg:w-64 flex-shrink-0">
          <div className="glass-panel rounded-2xl p-3 h-full">
            <div className="text-center mb-2">
              <div className="text-[10px] uppercase tracking-widest text-amber-300/70">Ödül</div>
              <div className="text-xl font-bold text-amber-200 tabular-nums">
                {currentPrize.toLocaleString('tr-TR')} ₺
              </div>
            </div>
            <MoneyTree levels={tree} currentIndex={levelIndex} lost={phase === 'lost'} />
          </div>
        </aside>

        {/* Main play area */}
        <main className="flex-1 flex flex-col">
          {/* Top bar */}
          <header className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-gradient-to-br from-amber-400 to-amber-600 flex items-center justify-center text-night-900 font-bold">
                {profile.avatar}
              </div>
              <div>
                <div className="text-sm font-semibold text-white">{profile.username}</div>
                <div className="text-xs text-cyan-300/70">Seviye {profile.level} · {profile.xp} XP</div>
              </div>
            </div>
            <button
              type="button"
              onClick={quitGame}
              className="px-4 py-2 rounded-xl border border-white/15 bg-white/5 hover:bg-white/10 text-white/80 text-sm transition"
            >
              <i className="fa-solid fa-door-open mr-1" /> Çekil
            </button>
          </header>

          {/* Timer */}
          <div className="flex justify-center mb-4">
            <TimerRing total={QUESTION_TIME} remaining={timeLeft} danger={timeLeft <= 5} />
          </div>

          {/* Question card */}
          {question && (
            <div className="glass-panel rounded-2xl p-5 mb-4 mx-auto max-w-2xl w-full">
              <div className="flex items-center justify-between mb-3 text-xs">
                <span className="px-2.5 py-1 rounded-full bg-cyan-500/20 text-cyan-200 border border-cyan-400/30">
                  {question.category}
                </span>
                <span className="px-2.5 py-1 rounded-full bg-amber-500/20 text-amber-200 border border-amber-400/30">
                  {question.difficulty}
                </span>
              </div>
              <p className="text-lg lg:text-xl text-white text-center leading-relaxed font-medium">
                {question.question}
              </p>
            </div>
          )}

          {/* Audience chart */}
          {audienceVotes && (
            <div className="max-w-2xl mx-auto w-full mb-4">
              <AudienceChart
                votes={audienceVotes}
                eliminated={eliminated}
                correctIndex={correctIndex}
                revealed={phase === 'correct' || phase === 'wrong'}
              />
            </div>
          )}

          {/* Answer options */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 max-w-2xl mx-auto w-full mb-4">
            {options.map((opt, i) => {
              const isSel = selected.includes(i);
              const isElim = eliminated.includes(i);
              const showCorrect = (phase === 'correct' || phase === 'wrong' || phase === 'revealing') && opt.isCorrect;
              const showWrong = phase === 'wrong' && isSel && !opt.isCorrect;
              const cls = isElim
                ? 'opacity-30 border-white/10 bg-white/5'
                : showCorrect
                  ? 'border-emerald-400 bg-emerald-500/25 text-emerald-100 shadow-emerald-glow'
                  : showWrong
                    ? 'border-red-500 bg-red-500/25 text-red-100 shadow-red-glow animate-shake'
                    : isSel
                      ? 'border-amber-400 bg-amber-400/20 text-amber-100'
                      : 'border-white/15 bg-white/5 hover:bg-white/10 hover:border-cyan-400/50';
              return (
                <button
                  key={i}
                  type="button"
                  disabled={isElim || locked}
                  onClick={() => selectOption(i)}
                  className={`flex items-center gap-3 rounded-xl border px-4 py-3.5 text-left transition-all duration-300 backdrop-blur-md ${cls}`}
                >
                  <span className="w-7 h-7 rounded-lg bg-white/10 flex items-center justify-center font-bold text-sm">
                    {letters[i]}
                  </span>
                  <span className="font-medium text-white/95">{opt.text}</span>
                </button>
              );
            })}
          </div>

          {/* Jokers */}
          <div className="mt-auto">
            <JokerPanel jokers={jokers} onUse={useJoker} disabled={locked} />
            {doubleActive && selected.length < 2 && (
              <p className="text-center text-xs text-cyan-300/80 mt-2">
                İki seçenek seçin ({selected.length}/2)
              </p>
            )}
          </div>
        </main>
      </div>

      {/* Win overlay */}
      <Confetti active={showWin} />
      {showWin && (
        <div className="fixed inset-0 z-40 flex items-center justify-center bg-night-900/80 backdrop-blur-md">
          <div className="glass-panel rounded-3xl p-8 max-w-md text-center animate-pop">
            <i className="fa-solid fa-crown text-6xl text-amber-400 mb-3 animate-bounce-slow" />
            <h2 className="text-3xl font-bold text-amber-200 mb-2">BÜYÜK ÖDÜL!</h2>
            <p className="text-5xl font-bold text-emerald-300 mb-4 tabular-nums">
              {currentPrize.toLocaleString('tr-TR')} ₺
            </p>
            <p className="text-white/70 mb-6">Tüm soruları doğru yanıtladınız!</p>
            <button
              type="button"
              onClick={() => onExit(profile)}
              className="px-6 py-3 rounded-xl bg-gradient-to-r from-amber-400 to-amber-600 text-night-900 font-bold hover:scale-105 transition"
            >
              Ana Menü
            </button>
          </div>
        </div>
      )}

      {/* Lose overlay */}
      {showLose && (
        <div className="fixed inset-0 z-40 flex items-center justify-center bg-night-900/80 backdrop-blur-md">
          <div className="glass-panel rounded-3xl p-8 max-w-md text-center animate-pop">
            <i className="fa-solid fa-heart-crack text-6xl text-red-400 mb-3" />
            <h2 className="text-3xl font-bold text-red-300 mb-2">KAYBETTİN</h2>
            <p className="text-2xl text-white/80 mb-1">Kazanılan:</p>
            <p className="text-3xl font-bold text-emerald-300 mb-6 tabular-nums">
              {getSafeHavenAmount(tree, levelIndex).toLocaleString('tr-TR')} ₺
            </p>
            <button
              type="button"
              onClick={() => onExit(profile)}
              className="px-6 py-3 rounded-xl bg-gradient-to-r from-red-500 to-red-700 text-white font-bold hover:scale-105 transition"
            >
              Tekrar Başlat
            </button>
          </div>
        </div>
      )}

      {/* Toasts */}
      {achievementToast && (
        <div className="fixed top-6 right-6 z-50 glass-panel rounded-xl px-4 py-3 max-w-xs animate-slide-in">
          <div className="flex items-center gap-2">
            <i className="fa-solid fa-trophy text-amber-400" />
            <div>
              <div className="text-xs text-amber-300 font-semibold">Başarım Açıldı</div>
              <div className="text-sm text-white">{achievementToast}</div>
            </div>
          </div>
        </div>
      )}
      {levelUpToast && (
        <div className="fixed top-6 left-6 z-50 glass-panel rounded-xl px-4 py-3 animate-slide-in">
          <div className="flex items-center gap-2">
            <i className="fa-solid fa-star text-cyan-300" />
            <span className="text-sm text-white">{levelUpToast}</span>
          </div>
        </div>
      )}
    </div>
  );
}
