"use client";

import Link from "next/link";

import { useCurrentUser } from "@/components/auth/require-sign-in";
import { LiveIndicator } from "@/components/header/live-indicator";
import { MeetingStatus } from "@/components/header/meeting-status";
import { TeamSwitcher } from "@/components/header/team-switcher";
import { UserMenu } from "@/components/header/user-menu";
import { Badge } from "@/components/ui/badge";
import type { LiveStatus } from "@/lib/live/use-live-team";
import { canChangeTeam } from "@/lib/permissions";

type AppHeaderProps = {
  teamId: string;
  teamLoaded: boolean;
  liveStatus: LiveStatus;
};

export function AppHeader({ teamId, teamLoaded, liveStatus }: AppHeaderProps) {
  const me = useCurrentUser();

  return (
    <header className="flex h-14 items-center gap-4 border-b bg-muted/40 px-4 lg:h-[60px] lg:px-6">
      <Link href="/" className="font-semibold">
        Level 10
      </Link>
      <TeamSwitcher teamId={teamId} />
      {teamLoaded && !canChangeTeam(me, teamId) && <Badge variant="outline">Read-only</Badge>}
      <div className="ml-auto flex items-center gap-4">
        {teamLoaded && <MeetingStatus teamId={teamId} />}
        {teamLoaded && <LiveIndicator status={liveStatus} />}
        <UserMenu />
      </div>
    </header>
  );
}
