const BACKEND_URL = process.env.BACKEND_URL ?? "http://localhost:8000";

export async function GET(request: Request) {
  const { search } = new URL(request.url);
  const backendResponse = await fetch(`${BACKEND_URL}/notifications${search}`);
  const data = await backendResponse.json();
  return Response.json(data, { status: backendResponse.status });
}
