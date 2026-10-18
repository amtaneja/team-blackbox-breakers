import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import DashboardWorkspace from "./dashboard-workspace";

export default async function DashboardPage() {
  const session = await cookies();
  if (session.get("bb-demo-session")?.value !== "authenticated") {
    redirect("/login");
  }

  return <DashboardWorkspace />;
}
