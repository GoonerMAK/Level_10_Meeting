"use client";

import { useQuery } from "@tanstack/react-query";

import { api } from "./client";
import { readData } from "./errors";
import { queryKeys } from "./query-keys";

export const useRocks = (teamId: string) =>
  useQuery({
    queryKey: queryKeys.rocks(teamId),
    queryFn: () => readData(api.GET("/api/teams/{team_id}/rocks", { params: { path: { team_id: teamId } } })),
  });
