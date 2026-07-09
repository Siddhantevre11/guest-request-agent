const BACKEND_URL = process.env.BACKEND_URL ?? "http://localhost:8000";

export async function POST(request: Request) {
  const body = await request.text();
  const backendResponse = await fetch(`${BACKEND_URL}/message`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body,
  });
  const data = await backendResponse.json();
  return Response.json(data, { status: backendResponse.status });
}
