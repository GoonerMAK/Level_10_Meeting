"use client";

import { User } from "lucide-react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";

import { useCurrentUser } from "@/components/auth/require-sign-in";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useSignOut } from "@/lib/api/auth";
import { errorMessage } from "@/lib/api/errors";
import { ROLE_LABELS } from "@/lib/permissions";

export function UserMenu() {
  const me = useCurrentUser();
  const signOut = useSignOut();
  const router = useRouter();

  const handleSignOut = () =>
    signOut.mutate(undefined, {
      onSuccess: () => router.replace("/sign-in"),
      onError: (error) => toast.error(errorMessage(error)),
    });

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="secondary" size="icon" className="rounded-full border">
          <User />
          <span className="sr-only">Open user menu</span>
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="min-w-56">
        <DropdownMenuLabel className="flex flex-col gap-0.5">
          <span className="text-sm font-medium text-foreground">{me.name}</span>
          <span className="text-xs font-normal">
            {ROLE_LABELS[me.role]} · {me.email}
          </span>
        </DropdownMenuLabel>
        <DropdownMenuSeparator />
        <DropdownMenuItem onSelect={() => router.push("/sign-in")}>Switch user</DropdownMenuItem>
        <DropdownMenuItem onSelect={handleSignOut} disabled={signOut.isPending}>
          Sign out
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
