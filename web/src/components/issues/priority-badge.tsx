import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

const PRIORITY_STYLES: Record<number, string> = {
  5: "border-transparent bg-primary text-primary-foreground",
  4: "border-transparent bg-stone-600 text-white",
  3: "border-transparent bg-stone-200 text-stone-900",
};

export function PriorityBadge({ priority }: { priority: number | null }) {
  return (
    <Badge
      variant="outline"
      aria-label={priority === null ? "No priority" : `Priority ${priority}`}
      className={cn("w-9 justify-center tabular-nums", priority === null ? "text-muted-foreground" : PRIORITY_STYLES[priority])}
    >
      {priority === null ? "—" : `P${priority}`}
    </Badge>
  );
}
