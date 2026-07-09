const BACKEND_URL = process.env.BACKEND_URL ?? "http://localhost:8000";

export async function GET() {
  const backendResponse = await fetch(`${BACKEND_URL}/host/approvals`);
  const data = await backendResponse.json();
  return Response.json(data, { status: backendResponse.status });
}
