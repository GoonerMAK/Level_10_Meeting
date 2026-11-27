"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "./client";
import { readData } from "./errors";
import { queryKeys } from "./query-keys";

export const useTodos = (teamId: string) =>
  useQuery({
    queryKey: queryKeys.teamData(teamId, "todos"),
    queryFn: () => readData(api.GET("/api/teams/{team_id}/todos", { params: { path: { team_id: teamId } } })),
  });

export function useSetTodoDone(teamId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ todoId, done }: { todoId: string; done: boolean }) => {
      const options = { params: { path: { todo_id: todoId } } };
      return readData(done ? api.POST("/api/todos/{todo_id}/done", options) : api.POST("/api/todos/{todo_id}/undo", options));
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: queryKeys.teamData(teamId, "todos") }),
  });
}
