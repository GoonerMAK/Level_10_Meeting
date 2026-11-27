import { QueryCache, QueryClient } from "@tanstack/react-query";

import { isApiError } from "./api/errors";
import { queryKeys } from "./api/query-keys";

const MAX_RETRIES = 2;

export const shouldRetry = (failureCount: number, error: unknown): boolean =>
  failureCount < MAX_RETRIES && !(isApiError(error) && error.status < 500);

export function makeQueryClient(): QueryClient {
  const queryClient: QueryClient = new QueryClient({
    queryCache: new QueryCache({
      onError: (error) => {
        if (isApiError(error, 401)) {
          queryClient.setQueryData(queryKeys.me, null);
        }
      },
    }),
    defaultOptions: {
      queries: { staleTime: 30_000, retry: shouldRetry },
      mutations: { retry: false },
    },
  });
  return queryClient;
}
