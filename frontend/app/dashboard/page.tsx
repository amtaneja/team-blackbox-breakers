import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import { isValidSessionToken, SESSION_COOKIE } from "@/lib/demo-session";
import DashboardWorkspace from "./dashboard-workspace";

export default async function DashboardPage() {
  const session = await cookies();
  if (!isValidSessionToken(session.get(SESSION_COOKIE)?.value)) {
    redirect("/login");
  }

  return <DashboardWorkspace />;
}
