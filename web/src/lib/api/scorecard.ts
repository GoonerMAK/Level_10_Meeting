"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api, type Issue, type Scorecard, type ScoreCell } from "./client";
import { readData, toApiError } from "./errors";
import { queryKeys } from "./query-keys";

type ScoreTarget = { measurableId: string; weekStart: string };

const scorePath = ({ measurableId, weekStart }: ScoreTarget) => ({
  params: { path: { measurable_id: measurableId, week_start: weekStart } },
});

export const useScorecard = (teamId: string) =>
  useQuery({
    queryKey: queryKeys.teamData(teamId, "scorecard"),
    queryFn: () => readData(api.GET("/api/teams/{team_id}/scorecard", { params: { path: { team_id: teamId } } })),
  });

export const replaceCell = (scorecard: Scorecard, measurableId: string, cell: ScoreCell): Scorecard => ({
  ...scorecard,
  measurables: scorecard.measurables.map((measurable) =>
    measurable.id === measurableId
      ? {
          ...measurable,
          cells: measurable.cells.map((current) => (current.week_start === cell.week_start ? cell : current)),
        }
      : measurable,
  ),
});

export function useUpdateScore(teamId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ value, ...target }: ScoreTarget & { value: string }) =>
      readData(api.PUT("/api/measurables/{measurable_id}/scores/{week_start}", { ...scorePath(target), body: { value } })),
    onSuccess: (cell, { measurableId }) => {
      queryClient.setQueryData<Scorecard>(queryKeys.teamData(teamId, "scorecard"), (scorecard) =>
        scorecard ? replaceCell(scorecard, measurableId, cell) : scorecard,
      );
    },
  });
}

async function makeIssue(target: ScoreTarget): Promise<{ issue: Issue; created: boolean }> {
  const { data, error, response } = await api.POST(
    "/api/measurables/{measurable_id}/scores/{week_start}/issue",
    scorePath(target),
  );
  if (!response.ok || data === undefined) {
    throw toApiError(response.status, error);
  }
  return { issue: data, created: response.status === 201 };
}

export function useMakeIssue(teamId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: makeIssue,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: queryKeys.teamData(teamId, "issues") }),
  });
}
