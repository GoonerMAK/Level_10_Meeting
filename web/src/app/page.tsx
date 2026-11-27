import { FirstTeamRedirect } from "@/components/auth/first-team-redirect";
import { RequireSignIn } from "@/components/auth/require-sign-in";

export default function Home() {
  return (
    <RequireSignIn>
      <FirstTeamRedirect />
    </RequireSignIn>
  );
}
