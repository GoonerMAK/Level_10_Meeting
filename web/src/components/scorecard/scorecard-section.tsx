"use client";

import { ErrorState } from "@/components/error-state";
import { ScoreCellView } from "@/components/scorecard/score-cell";
import { SectionCard } from "@/components/section-card";
import { useTeamContext } from "@/components/team/team-context";
import { Skeleton } from "@/components/ui/skeleton";
import { errorMessage } from "@/lib/api/errors";
import { useScorecard } from "@/lib/api/scorecard";
import { formatDate, formatGoal } from "@/lib/format";
import { cn } from "@/lib/utils";

export function ScorecardSection() {
  const { teamId, canChange } = useTeamContext();
  const scorecard = useScorecard(teamId);

  const renderBody = () => {
    if (scorecard.isPending) {
      return <Skeleton aria-label="Loading Scorecard" className="h-48 w-full" />;
    }
    if (scorecard.isError) {
      return <ErrorState message={errorMessage(scorecard.error)} onRetry={() => void scorecard.refetch()} />;
    }
    const { weeks, current_week: currentWeek, measurables } = scorecard.data;
    if (measurables.length === 0) {
      return <p className="text-sm text-muted-foreground">This team has no Measurables.</p>;
    }
    return (
      <div className="overflow-x-auto">
        <table className="w-full border-separate border-spacing-0.5 text-sm">
          <thead>
            <tr className="text-xs text-muted-foreground">
              <th scope="col" className="sticky left-0 z-10 min-w-48 bg-card px-2 py-1 text-left font-medium">
                Measurable
              </th>
              <th scope="col" className="px-2 py-1 text-left font-medium whitespace-nowrap">
                Goal
              </th>
              {weeks.map((week) => (
                <th
                  key={week}
                  scope="col"
                  className={cn(
                    "min-w-16 px-1 py-1 text-center font-medium whitespace-nowrap",
                    week === currentWeek && "text-foreground",
                  )}
                >
                  {formatDate(week)}
                  {week === currentWeek && <span className="block text-[10px] font-normal">This week</span>}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {measurables.map((measurable) => (
              <tr key={measurable.id}>
                <th scope="row" className="sticky left-0 z-10 bg-card px-2 py-1 text-left font-normal">
                  <span className="block font-medium">{measurable.name}</span>
                  <span className="block text-xs text-muted-foreground">{measurable.owner.name}</span>
                </th>
                <td className="px-2 py-1 text-xs whitespace-nowrap text-muted-foreground">
                  {formatGoal(measurable.goal, measurable.unit)}
                </td>
                {measurable.cells.map((cell) => (
                  <td key={cell.week_start} className="p-0">
                    <ScoreCellView measurable={measurable} cell={cell} />
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  };

  return (
    <SectionCard
      title="Scorecard"
      description={canChange ? "Last 13 weeks. Click a score to edit it; flag an off-track one to make it an Issue." : "Last 13 weeks"}
    >
      {renderBody()}
    </SectionCard>
  );
}
