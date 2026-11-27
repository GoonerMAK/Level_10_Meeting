import { Badge } from "@/components/ui/badge";
import type { MeetingState } from "@/lib/api/client";

export function AttendeeList({ meeting, meId }: { meeting: MeetingState; meId: string }) {
  return (
    <div className="flex flex-wrap items-center gap-2 text-sm">
      <span className="text-muted-foreground">Attendees ({meeting.attendees.length})</span>
      <ul aria-label="Attendees" className="flex flex-wrap gap-1.5">
        {meeting.attendees.map((attendee) => (
          <li key={attendee.id}>
            <Badge variant={attendee.id === meeting.facilitator.id ? "default" : "secondary"}>
              {attendee.name}
              {attendee.id === meId && " (you)"}
              {attendee.id === meeting.facilitator.id && " · Facilitator"}
            </Badge>
          </li>
        ))}
      </ul>
    </div>
  );
}
