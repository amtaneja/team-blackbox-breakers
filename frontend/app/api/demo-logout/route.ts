import { NextResponse } from "next/server";

export async function GET() {
  const response = new NextResponse(null, {
    status: 303,
    headers: { Location: "/" },
  });
  response.cookies.delete("bb-demo-session");
  return response;
}
