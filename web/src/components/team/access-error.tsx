"use client";

import Link from "next/link";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useTeams } from "@/lib/api/teams";

export function AccessError({ message }: { message: string }) {
  const teams = useTeams();

  return (
    <Card role="alert" className="mx-auto mt-10 max-w-md">
      <CardHeader>
        <CardTitle>You can&apos;t open this team</CardTitle>
        <CardDescription>{message}. It may not exist, or you aren&apos;t a member.</CardDescription>
      </CardHeader>
      {teams.data && teams.data.length > 0 && (
        <CardContent className="flex flex-wrap gap-2">
          {teams.data.map((team) => (
            <Button key={team.id} variant="outline" size="sm" asChild>
              <Link href={`/teams/${team.id}`}>{team.name}</Link>
            </Button>
          ))}
        </CardContent>
      )}
    </Card>
  );
}
