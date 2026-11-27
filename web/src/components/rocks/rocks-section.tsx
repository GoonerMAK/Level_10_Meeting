"use client";

import { CheckCircle2, Circle } from "lucide-react";

import { ErrorState } from "@/components/error-state";
import { SectionCard } from "@/components/section-card";
import { ROCK_STATUS } from "@/components/team/status";
import { useTeamContext } from "@/components/team/team-context";
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Skeleton } from "@/components/ui/skeleton";
import type { Rock } from "@/lib/api/client";
import { errorMessage } from "@/lib/api/errors";
import { useRocks } from "@/lib/api/rocks";
import { formatDate, formatQuarter } from "@/lib/format";
import { cn } from "@/lib/utils";

export function RocksSection() {
  const { teamId } = useTeamContext();
  const rocks = useRocks(teamId);

  const renderBody = () => {
    if (rocks.isPending) {
      return <Skeleton aria-label="Loading Rocks" className="h-32 w-full" />;
    }
    if (rocks.isError) {
      return <ErrorState message={errorMessage(rocks.error)} onRetry={() => void rocks.refetch()} />;
    }
    if (rocks.data.rocks.length === 0) {
      return <p className="text-sm text-muted-foreground">No Rocks this quarter.</p>;
    }
    return (
      <Accordion type="multiple">
        {rocks.data.rocks.map((rock) => (
          <RockItem key={rock.id} rock={rock} />
        ))}
      </Accordion>
    );
  };

  return (
    <SectionCard title="Rocks" description={rocks.data && `${formatQuarter(rocks.data.quarter)} · expand a Rock to see its Milestones`}>
      {renderBody()}
    </SectionCard>
  );
}

function RockItem({ rock }: { rock: Rock }) {
  const status = ROCK_STATUS[rock.status];

  return (
    <AccordionItem value={rock.id}>
      <AccordionTrigger className="items-center gap-3 hover:no-underline">
        <span className="flex min-w-0 flex-1 flex-col">
          <span className="font-medium">{rock.title}</span>
          <span className="text-xs font-normal text-muted-foreground">{rock.owner.name}</span>
        </span>
        <Badge variant="outline" className={status.badge}>
          {status.label}
        </Badge>
        <span className="flex w-28 items-center gap-2">
          <Progress value={rock.progress_percent} aria-label={`${rock.title} progress`} className="h-1.5" />
          <span className="w-9 text-right text-xs font-normal tabular-nums">{rock.progress_percent}%</span>
        </span>
      </AccordionTrigger>
      <AccordionContent>
        {rock.milestones.length === 0 ? (
          <p className="text-xs text-muted-foreground">No Milestones.</p>
        ) : (
          <ul className="flex flex-col gap-1.5">
            {rock.milestones.map((milestone) => (
              <li key={milestone.id} className="flex items-start justify-between gap-3">
                <span className="flex items-start gap-2">
                  {milestone.done ? (
                    <CheckCircle2 aria-label="Done" className="mt-0.5 size-4 shrink-0 text-emerald-600" />
                  ) : (
                    <Circle aria-label="Not done" className="mt-0.5 size-4 shrink-0 text-muted-foreground" />
                  )}
                  <span className={cn(milestone.done && "text-muted-foreground")}>{milestone.title}</span>
                </span>
                <span className="text-xs whitespace-nowrap text-muted-foreground">Due {formatDate(milestone.due_date)}</span>
              </li>
            ))}
          </ul>
        )}
      </AccordionContent>
    </AccordionItem>
  );
}
