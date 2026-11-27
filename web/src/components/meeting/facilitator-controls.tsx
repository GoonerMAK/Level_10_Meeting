"use client";

import { ArrowRight } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import type { MeetingState } from "@/lib/api/client";
import { errorMessage } from "@/lib/api/errors";
import { useEndMeeting, useNextSection } from "@/lib/api/meetings";
import { nextSection, SECTION_LABELS, type MeetingSection } from "@/lib/meeting-clock";

export function FacilitatorControls({ meeting, section }: { meeting: MeetingState; section: MeetingSection }) {
  const nextSectionMutation = useNextSection(meeting.team_id);
  const following = nextSection(section);
  const showError = (error: unknown) => toast.error(errorMessage(error));

  return (
    <div className="flex items-center gap-2">
      {following && (
        <Button
          size="lg"
          disabled={nextSectionMutation.isPending}
          onClick={() =>
            nextSectionMutation.mutate({ meetingId: meeting.id, fromSection: section }, { onError: showError })
          }
        >
          Next: {SECTION_LABELS[following]}
          <ArrowRight aria-hidden />
        </Button>
      )}
      <EndMeetingButton meeting={meeting} prominent={!following} />
    </div>
  );
}

function EndMeetingButton({ meeting, prominent }: { meeting: MeetingState; prominent: boolean }) {
  const endMeeting = useEndMeeting(meeting.team_id);
  const [open, setOpen] = useState(false);

  const end = () =>
    endMeeting.mutate(meeting.id, {
      onSuccess: () => setOpen(false),
      onError: (error) => toast.error(errorMessage(error)),
    });

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button size="lg" variant={prominent ? "default" : "outline"}>
          End meeting
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>End the meeting for everyone?</DialogTitle>
          <DialogDescription>Ratings lock and every attendee sees the summary.</DialogDescription>
        </DialogHeader>
        <DialogFooter>
          <DialogClose asChild>
            <Button variant="outline">Keep going</Button>
          </DialogClose>
          <Button variant="destructive" onClick={end} disabled={endMeeting.isPending}>
            End meeting
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
