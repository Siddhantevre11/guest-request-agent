import { afterEach, describe, expect, it, vi } from "vitest";

describe("POST /api/message", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    vi.resetModules();
  });

  it("forwards the guest message to the backend and returns its reply", async () => {
    const backendResponse = { reply: "The wifi password is SunnyDays2024!." };
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => backendResponse,
    });
    vi.stubGlobal("fetch", fetchMock);

    const { POST } = await import("./route");
    const request = new Request("http://localhost/api/message", {
      method: "POST",
      body: JSON.stringify({ guest_id: "guest-1", conversation_id: "conv-1", message: "wifi password?" }),
    });

    const response = await POST(request);
    const body = await response.json();

    expect(body).toEqual(backendResponse);
    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining("/message"),
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ guest_id: "guest-1", conversation_id: "conv-1", message: "wifi password?" }),
      }),
    );
  });
});
