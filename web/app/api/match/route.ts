// A proxy, not logic. The browser posts here, this posts to FastAPI. Ranking happens there,
// in SQL and Python, and nothing on this side reorders the result.

import { NextRequest, NextResponse } from "next/server";

const BASE = process.env.API_URL ?? "http://127.0.0.1:8000";

export async function POST(req: NextRequest) {
  const body = await req.text();
  try {
    const res = await fetch(`${BASE}/api/match`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body,
      cache: "no-store",
    });
    return new NextResponse(await res.text(), {
      status: res.status,
      headers: { "content-type": "application/json" },
    });
  } catch {
    return NextResponse.json({ detail: `cannot reach the API at ${BASE}` }, { status: 502 });
  }
}
