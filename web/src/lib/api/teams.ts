"use client";

import { skipToken, useQuery } from "@tanstack/react-query";

import { api, type MeetingState } from "./client";
import { readData } from "./errors";
import { queryKeys } from "./query-keys";

export const readTeams = () => readData(api.GET("/api/teams"));

export const useTeams = () => useQuery({ queryKey: queryKeys.teams, queryFn: readTeams });

export const useTeam = (teamId: string) =>
  useQuery({
    queryKey: queryKeys.teamDetail(teamId),
    queryFn: () => readData(api.GET("/api/teams/{team_id}", { params: { path: { team_id: teamId } } })),
  });

export const useActiveMeeting = (teamId: string) =>
  useQuery<MeetingState | null>({ queryKey: queryKeys.activeMeeting(teamId), queryFn: skipToken });
