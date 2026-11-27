"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "./client";
import { readData } from "./errors";
import { queryKeys, type IssueStatus } from "./query-keys";

export const useIssues = (teamId: string, status: IssueStatus, { enabled = true }: { enabled?: boolean } = {}) =>
  useQuery({
    enabled,
    queryKey: queryKeys.issues(teamId, status),
    queryFn: () =>
      readData(api.GET("/api/teams/{team_id}/issues", { params: { path: { team_id: teamId }, query: { status } } })),
  });

function useRefreshIssues(teamId: string) {
  const queryClient = useQueryClient();
  return () => queryClient.invalidateQueries({ queryKey: queryKeys.teamData(teamId, "issues") });
}

export function useCreateIssue(teamId: string) {
  const refresh = useRefreshIssues(teamId);
  return useMutation({
    mutationFn: (body: { title: string; priority: number | null }) =>
      readData(api.POST("/api/teams/{team_id}/issues", { params: { path: { team_id: teamId } }, body })),
    onSuccess: refresh,
  });
}

export function useSetPriority(teamId: string) {
  const refresh = useRefreshIssues(teamId);
  return useMutation({
    mutationFn: ({ issueId, priority }: { issueId: string; priority: number | null }) =>
      readData(api.PATCH("/api/issues/{issue_id}", { params: { path: { issue_id: issueId } }, body: { priority } })),
    onSuccess: refresh,
  });
}

export function useSolveIssue(teamId: string) {
  const refresh = useRefreshIssues(teamId);
  return useMutation({
    mutationFn: ({ issueId, note }: { issueId: string; note: string }) =>
      readData(
        api.POST("/api/issues/{issue_id}/solve", {
          params: { path: { issue_id: issueId } },
          body: { resolution_note: note },
        }),
      ),
    onSuccess: refresh,
  });
}

export function useAddTodo(teamId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ issueId, title, ownerId }: { issueId: string; title: string; ownerId: string }) =>
      readData(
        api.POST("/api/issues/{issue_id}/todos", {
          params: { path: { issue_id: issueId } },
          body: { title, owner_id: ownerId },
        }),
      ),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: queryKeys.teamData(teamId, "todos") }),
  });
}
