"use client";

import { useEffect, useState } from "react";

import { useServerClockOffset } from "@/lib/api/meetings";

const TICK_MS = 250;

export function useServerNow(): number {
  const offset = useServerClockOffset();
  const [deviceNow, setDeviceNow] = useState(() => Date.now());

  useEffect(() => {
    const timer = setInterval(() => setDeviceNow(Date.now()), TICK_MS);
    return () => clearInterval(timer);
  }, []);

  return deviceNow + offset;
}
