"use client";

import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { useCallback } from "react";

const ISSUE_PARAM = "issue";

export function useOpenIssue(): (issueId: string) => void {
  const router = useRouter();
  const pathname = usePathname();
  return useCallback(
    (issueId: string) => router.push(`${pathname}?${ISSUE_PARAM}=${encodeURIComponent(issueId)}`, { scroll: false }),
    [router, pathname],
  );
}

export function useSelectedIssue(): { issueId: string | null; closeIssue: () => void } {
  const searchParams = useSearchParams();
  const router = useRouter();
  const pathname = usePathname();
  const closeIssue = useCallback(() => router.replace(pathname, { scroll: false }), [router, pathname]);
  return { issueId: searchParams.get(ISSUE_PARAM), closeIssue };
}
