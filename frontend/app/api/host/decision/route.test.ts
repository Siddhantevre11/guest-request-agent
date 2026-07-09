import { afterEach, describe, expect, it, vi } from "vitest";

describe("POST /api/host/decision", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("forwards the host's decision to the backend and returns its result", async () => {
    const backendResponse = { status: "approved", guest_notification: "Great news!", booking: { checkout_time: "13:00" } };
    const fetchMock = vi.fn().mockResolvedValue({ ok: true, json: async () => backendResponse });
    vi.stubGlobal("fetch", fetchMock);

    const { POST } = await import("./route");
    const request = new Request("http://localhost/api/host/decision", {
      method: "POST",
      body: JSON.stringify({ approval_id: "APR-1", decision: "approve" }),
    });

    const response = await POST(request);
    const body = await response.json();

    expect(body).toEqual(backendResponse);
    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining("/host/decision"),
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ approval_id: "APR-1", decision: "approve" }),
      }),
    );
  });
});
