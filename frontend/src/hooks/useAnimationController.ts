import { useCallback, useEffect, useMemo, useRef, useState } from "react";

export const ANIMATION_SPEEDS = [0.25, 0.5, 1, 2, 4, 8] as const;
export type AnimationSpeed = (typeof ANIMATION_SPEEDS)[number];

export type AnimationController<T> = {
  index: number;
  item: T | undefined;
  count: number;
  progress: number;
  isPlaying: boolean;
  isComplete: boolean;
  speed: AnimationSpeed;
  play: () => void;
  pause: () => void;
  resume: () => void;
  restart: () => void;
  stepForward: () => void;
  stepBackward: () => void;
  fastForward: () => void;
  finish: () => void;
  setSpeed: (speed: AnimationSpeed) => void;
};

type AnimationOptions = {
  baseDelayMs?: number;
  initialSpeed?: AnimationSpeed;
  autoPlay?: boolean;
};

/**
 * A single-timer replay controller. The controller deliberately owns one
 * cursor, allowing several visualizations to derive their current frame from
 * the same timeline while shorter traces remain on their completed frame.
 */
export function useAnimationController<T>(items: readonly T[], options: AnimationOptions = {}): AnimationController<T> {
  const baseDelayMs = options.baseDelayMs ?? 420;
  const count = items.length;
  const [index, setIndex] = useState(0);
  const [isPlaying, setIsPlaying] = useState(options.autoPlay ?? false);
  const [speed, setSpeedState] = useState<AnimationSpeed>(options.initialSpeed ?? 1);
  const generationRef = useRef(0);

  useEffect(() => {
    setIndex((current) => (count === 0 ? 0 : Math.min(current, count - 1)));
  }, [count]);

  useEffect(() => {
    if (!isPlaying || count <= 1 || index >= count - 1) {
      if (index >= count - 1 && isPlaying) setIsPlaying(false);
      return undefined;
    }

    const generation = generationRef.current + 1;
    generationRef.current = generation;
    const timer = window.setTimeout(() => {
      if (generationRef.current !== generation) return;
      setIndex((current) => Math.min(current + 1, count - 1));
    }, baseDelayMs / speed);

    return () => {
      generationRef.current += 1;
      window.clearTimeout(timer);
    };
  }, [baseDelayMs, count, index, isPlaying, speed]);

  const play = useCallback(() => {
    if (count > 0) setIsPlaying(true);
  }, [count]);

  const pause = useCallback(() => setIsPlaying(false), []);
  const resume = useCallback(() => {
    if (count > 0 && index < count - 1) setIsPlaying(true);
  }, [count, index]);

  const restart = useCallback(() => {
    setIsPlaying(false);
    setIndex(0);
  }, []);

  const stepForward = useCallback(() => {
    setIsPlaying(false);
    setIndex((current) => Math.min(current + 1, Math.max(0, count - 1)));
  }, [count]);

  const stepBackward = useCallback(() => {
    setIsPlaying(false);
    setIndex((current) => Math.max(0, current - 1));
  }, []);

  const fastForward = useCallback(() => {
    if (count === 0) return;
    setSpeedState(8);
    setIsPlaying(true);
  }, [count]);

  const finish = useCallback(() => {
    setIsPlaying(false);
    setIndex(Math.max(0, count - 1));
  }, [count]);

  const setSpeed = useCallback((nextSpeed: AnimationSpeed) => setSpeedState(nextSpeed), []);

  return useMemo(() => ({
    index,
    item: items[index],
    count,
    progress: count <= 1 ? (count === 1 ? 100 : 0) : ((index + 1) / count) * 100,
    isPlaying,
    isComplete: count > 0 && index >= count - 1,
    speed,
    play,
    pause,
    resume,
    restart,
    stepForward,
    stepBackward,
    fastForward,
    finish,
    setSpeed,
  }), [count, finish, index, isPlaying, items, pause, play, restart, resume, setSpeed, speed, stepBackward, stepForward, fastForward]);
}
