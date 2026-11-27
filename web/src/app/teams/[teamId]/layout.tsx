import { TeamShell } from "@/components/team/team-shell";

export default function TeamLayout({ children }: LayoutProps<"/teams/[teamId]">) {
  return <TeamShell>{children}</TeamShell>;
}
