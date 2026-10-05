import { useEffect, useRef, useState } from "react";

import { getTimer } from "../api/timerClient";
import "./PhaseTimer.css";

const FINAL_WARNING_MS = 2 * 60 * 1000;

function format(ms) {
  const totalSeconds = Math.max(0, Math.ceil(ms / 1000));
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = String(totalSeconds % 60).padStart(2, "0");
  return `${minutes}:${seconds}`;
}

/**
 * Countdown for the current timed phase. The server owns the start time,
 * minimum, and limit; the browser only displays them (corrected for any
 * difference between the student's clock and the server's).
 *
 * onMinReached fires once when the student is allowed to move on.
 * onExpire fires once when time runs out.
 */
export default function PhaseTimer({ onExpire, onMinReached, showContinueNote = true }) {
  const [timer, setTimer] = useState(null);
  const [now, setNow] = useState(() => Date.now());
  const offsetRef = useRef(0);
  const expiredRef = useRef(false);
  const minReachedRef = useRef(false);
  const onExpireRef = useRef(onExpire);
  const onMinReachedRef = useRef(onMinReached);

  useEffect(() => {
    onExpireRef.current = onExpire;
    onMinReachedRef.current = onMinReached;
  }, [onExpire, onMinReached]);

  // Load the server timer. Retry briefly: the attempt/session row may still
  // be in the middle of being created when this screen first renders.
  useEffect(() => {
    let cancelled = false;
    let retryHandle;

    const load = async (attempt = 0) => {
      try {
        const data = await getTimer();
        if (cancelled) return;
        if (!data) {
          if (attempt < 30) retryHandle = setTimeout(() => load(attempt + 1), 1000);
          return;
        }
        offsetRef.current = Date.parse(data.server_now) - Date.now();
        const startedAt = Date.parse(data.started_at);
        setTimer({
          minAt: startedAt + data.min_time_seconds * 1000,
          deadline: startedAt + data.time_limit_seconds * 1000,
        });
      } catch {
        if (!cancelled && attempt < 30) {
          retryHandle = setTimeout(() => load(attempt + 1), 2000);
        }
      }
    };

    load();
    return () => {
      cancelled = true;
      clearTimeout(retryHandle);
    };
  }, []);

  useEffect(() => {
    if (!timer) return undefined;

    const tick = () => {
      const serverNow = Date.now() + offsetRef.current;
      setNow(serverNow);

      if (serverNow >= timer.minAt && !minReachedRef.current) {
        minReachedRef.current = true;
        onMinReachedRef.current?.();
      }
      if (serverNow >= timer.deadline && !expiredRef.current) {
        expiredRef.current = true;
        onExpireRef.current?.();
      }
    };

    tick();
    const handle = setInterval(tick, 250);
    return () => clearInterval(handle);
  }, [timer]);

  if (!timer) return null;

  const remaining = timer.deadline - now;
  const canContinue = now >= timer.minAt;
  const finalMinutes = remaining <= FINAL_WARNING_MS;

  return (
    <div className="phase-timer-wrap">
      {showContinueNote && canContinue && remaining > 0 && (
        <span className="phase-timer__note">You may continue to the next step.</span>
      )}
      <div
        className={`phase-timer${finalMinutes ? " phase-timer--final" : ""}`}
        role="timer"
        aria-live="off"
      >
        <span className="phase-timer__label">Time remaining</span>
        <span className="phase-timer__value">{format(remaining)}</span>
      </div>
    </div>
  );
}
