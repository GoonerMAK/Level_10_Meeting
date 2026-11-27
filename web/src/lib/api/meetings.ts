"use client";

import { skipToken, useMutation, useQuery, useQueryClient, type QueryClient } from "@tanstack/react-query";

import { api, type MeetingState, type Schemas } from "./client";
import { readData } from "./errors";
import { queryKeys, type SummaryStage } from "./query-keys";

type MeetingSection = Schemas["MeetingSection"];

export const isOlderSnapshot = (incoming: MeetingState | null, current: MeetingState | null | undefined): boolean =>
  incoming !== null &&
  current?.id === incoming.id &&
  Date.parse(incoming.server_now) < Date.parse(current.server_now);

export function storeMeeting(queryClient: QueryClient, teamId: string, incoming: MeetingState | null): void {
  const current = queryClient.getQueryData<MeetingState | null>(queryKeys.activeMeeting(teamId));
  if (isOlderSnapshot(incoming, current)) {
    return;
  }
  queryClient.setQueryData(queryKeys.activeMeeting(teamId), incoming);
  if (incoming) {
    queryClient.setQueryData(queryKeys.serverClockOffset, Date.parse(incoming.server_now) - Date.now());
  }
}

export const useServerClockOffset = (): number =>
  useQuery<number>({ queryKey: queryKeys.serverClockOffset, queryFn: skipToken }).data ?? 0;

function useMeetingMutation<Variables>(teamId: string, request: (variables: Variables) => Promise<MeetingState>) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: request,
    onSuccess: (meeting) => storeMeeting(queryClient, teamId, meeting),
  });
}

export const useStartMeeting = (teamId: string) =>
  useMeetingMutation(teamId, () =>
    readData(api.POST("/api/teams/{team_id}/meetings", { params: { path: { team_id: teamId } } })),
  );

export const useJoinMeeting = (teamId: string) =>
  useMeetingMutation(teamId, (meetingId: string) =>
    readData(api.POST("/api/meetings/{meeting_id}/join", { params: { path: { meeting_id: meetingId } } })),
  );

export const useNextSection = (teamId: string) =>
  useMeetingMutation(teamId, ({ meetingId, fromSection }: { meetingId: string; fromSection: MeetingSection }) =>
    readData(
      api.POST("/api/meetings/{meeting_id}/next", {
        params: { path: { meeting_id: meetingId } },
        body: { from_section: fromSection },
      }),
    ),
  );

export const useMeetingSummary = (teamId: string, meetingId: string, stage: SummaryStage) =>
  useQuery({
    queryKey: queryKeys.meetingSummary(teamId, meetingId, stage),
    queryFn: () =>
      readData(api.GET("/api/meetings/{meeting_id}/summary", { params: { path: { meeting_id: meetingId } } })),
  });

export const useRateMeeting = (teamId: string) =>
  useMeetingMutation(teamId, ({ meetingId, rating }: { meetingId: string; rating: number }) =>
    readData(
      api.PUT("/api/meetings/{meeting_id}/rating", { params: { path: { meeting_id: meetingId } }, body: { rating } }),
    ),
  );

export const useEndMeeting = (teamId: string) =>
  useMeetingMutation(teamId, (meetingId: string) =>
    readData(api.POST("/api/meetings/{meeting_id}/end", { params: { path: { meeting_id: meetingId } } })),
  );
