"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api, type Me } from "./client";
import { ensureOk, isApiError, readData } from "./errors";
import { queryKeys } from "./query-keys";

async function readMe(): Promise<Me | null> {
  try {
    return await readData(api.GET("/api/auth/me"));
  } catch (error) {
    if (isApiError(error, 401)) {
      return null;
    }
    throw error;
  }
}

export const useMe = () => useQuery({ queryKey: queryKeys.me, queryFn: readMe });

export const useSignInChoices = () =>
  useQuery({ queryKey: queryKeys.signInChoices, queryFn: () => readData(api.GET("/api/auth/users")) });

export function useSignIn() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (userId: string) => readData(api.POST("/api/auth/sign-in", { body: { user_id: userId } })),
    onSuccess: (me) => {
      queryClient.clear();
      queryClient.setQueryData(queryKeys.me, me);
    },
  });
}

export function useSignOut() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => ensureOk(api.POST("/api/auth/sign-out")),
    onSuccess: () => {
      queryClient.clear();
      queryClient.setQueryData(queryKeys.me, null);
    },
  });
}
