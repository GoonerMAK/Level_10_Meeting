"use client";

import { IssueDrawer } from "@/components/issues/issue-drawer";
import { IssuesSection } from "@/components/issues/issues-section";
import { RocksSection } from "@/components/rocks/rocks-section";
import { ScorecardSection } from "@/components/scorecard/scorecard-section";
import { useTeamContext } from "@/components/team/team-context";
import { TodosSection } from "@/components/todos/todos-section";

export function TeamPage() {
  const { teamName } = useTeamContext();

  return (
    <div className="flex flex-col gap-6">
      <h1 className="text-2xl font-semibold">{teamName}</h1>
      <ScorecardSection />
      <IssuesSection />
      <div className="grid items-start gap-6 lg:grid-cols-2">
        <TodosSection />
        <RocksSection />
      </div>
      <IssueDrawer />
    </div>
  );
}
