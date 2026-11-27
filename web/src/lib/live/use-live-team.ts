"use client";

import { useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";

import { queryKeys } from "../api/query-keys";
import { applyLiveMessage, parseLiveMessage } from "./messages";

export type LiveStatus = "connecting" | "live" | "reconnecting";

const FIRST_RETRY_MS = 1_000;
const MAX_RETRY_MS = 10_000;

export const retryDelay = (attempt: number): number => Math.min(FIRST_RETRY_MS * 2 ** attempt, MAX_RETRY_MS);

const liveUrl = (teamId: string): string => {
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  return `${protocol}//${window.location.host}/api/live?team_id=${encodeURIComponent(teamId)}`;
};

export function useLiveTeam({ teamId, enabled }: { teamId: string; enabled: boolean }): LiveStatus {
  const queryClient = useQueryClient();
  const [status, setStatus] = useState<LiveStatus>("connecting");

  useEffect(() => {
    if (!enabled) {
      return;
    }
    let socket: WebSocket | null = null;
    let retryTimer: ReturnType<typeof setTimeout> | undefined;
    let attempt = 0;
    let stopped = false;

    const connect = () => {
      socket = new WebSocket(liveUrl(teamId));
      socket.onopen = () => {
        if (attempt > 0) {
          void queryClient.invalidateQueries({ queryKey: queryKeys.team(teamId) });
        }
        attempt = 0;
        setStatus("live");
      };
      socket.onmessage = (event: MessageEvent<string>) => {
        const message = parseLiveMessage(event.data);
        if (message) {
          void applyLiveMessage({ queryClient, teamId, message });
        }
      };
      socket.onclose = () => {
        if (stopped) {
          return;
        }
        setStatus("reconnecting");
        retryTimer = setTimeout(connect, retryDelay(attempt));
        attempt += 1;
      };
    };

    connect();

    return () => {
      stopped = true;
      clearTimeout(retryTimer);
      socket?.close();
    };
  }, [teamId, enabled, queryClient]);

  return status;
}
