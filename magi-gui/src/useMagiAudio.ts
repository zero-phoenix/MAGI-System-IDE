import { useRef, useEffect } from 'react';

export function useMagiAudio() {
  const audioRef = useRef<HTMLAudioElement | null>(null);

  useEffect(() => {
    audioRef.current = new Audio('/magi_sound.mp3');
  }, []);

  const playCustomSound = () => {
    if (audioRef.current) {
      audioRef.current.currentTime = 0;
      audioRef.current.play().catch(e => console.error("Audio play failed", e));
    }
  };

  const playCalcBeep = () => {
    playCustomSound();
  };

  const playDecisionClack = () => {
    playCustomSound();
  };

  return { playCalcBeep, playDecisionClack };
}
