import { Check } from "lucide-react";

import { AGENDA, type MeetingSection } from "@/lib/meeting-clock";
import { cn } from "@/lib/utils";

export function AgendaSteps({ section }: { section: MeetingSection }) {
  const currentIndex = AGENDA.findIndex((item) => item.section === section);

  return (
    <ol aria-label="Agenda" className="flex flex-wrap items-center gap-2">
      {AGENDA.map((item, index) => {
        const done = index < currentIndex;
        const current = index === currentIndex;
        return (
          <li
            key={item.section}
            aria-current={current ? "step" : undefined}
            className={cn(
              "flex items-center gap-2 rounded-md border px-3 py-1.5 text-sm",
              current && "border-primary bg-primary text-primary-foreground",
              done && "text-muted-foreground",
            )}
          >
            <span
              aria-hidden
              className={cn(
                "flex size-5 items-center justify-center rounded-full border text-xs",
                current && "border-primary-foreground",
              )}
            >
              {done ? <Check className="size-3" /> : index + 1}
            </span>
            <span className="font-medium">{item.label}</span>
            <span className={cn("text-xs", current ? "text-primary-foreground/80" : "text-muted-foreground")}>
              {item.minutes} min
            </span>
            {done && <span className="sr-only">(done)</span>}
          </li>
        );
      })}
    </ol>
  );
}
