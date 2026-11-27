import { useId, type ReactNode } from "react";

import { cn } from "@/lib/utils";

type SectionCardProps = {
  title: string;
  description?: ReactNode;
  actions?: ReactNode;
  children: ReactNode;
  className?: string;
};

export function SectionCard({ title, description, actions, children, className }: SectionCardProps) {
  const headingId = useId();

  return (
    <section
      aria-labelledby={headingId}
      className={cn("min-w-0 rounded-lg border bg-card p-6 text-card-foreground shadow-sm", className)}
    >
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <div className="flex flex-col gap-0.5">
          <h2 id={headingId} className="text-lg font-semibold">
            {title}
          </h2>
          {description && <p className="text-xs text-muted-foreground">{description}</p>}
        </div>
        {actions}
      </div>
      {children}
    </section>
  );
}
