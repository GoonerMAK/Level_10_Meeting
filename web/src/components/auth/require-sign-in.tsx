"use client";

import { useRouter } from "next/navigation";
import { createContext, use, useEffect, type ReactNode } from "react";

import { ErrorState } from "@/components/error-state";
import { PageSkeleton } from "@/components/page-skeleton";
import { useMe } from "@/lib/api/auth";
import type { Me } from "@/lib/api/client";
import { errorMessage } from "@/lib/api/errors";

const CurrentUserContext = createContext<Me | null>(null);

export function RequireSignIn({ children }: { children: ReactNode }) {
  const me = useMe();
  const router = useRouter();
  const signedOut = me.data === null;

  useEffect(() => {
    if (signedOut) {
      router.replace("/sign-in");
    }
  }, [signedOut, router]);

  if (me.isError) {
    return <ErrorState className="p-6" message={errorMessage(me.error)} onRetry={() => void me.refetch()} />;
  }
  if (!me.data) {
    return <PageSkeleton />;
  }
  return <CurrentUserContext value={me.data}>{children}</CurrentUserContext>;
}

export function useCurrentUser(): Me {
  const me = use(CurrentUserContext);
  if (!me) {
    throw new Error("useCurrentUser must be used inside RequireSignIn");
  }
  return me;
}
