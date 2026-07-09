import { afterEach, describe, expect, it, vi } from "vitest";

describe("GET /api/host/escalations", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("returns the backend's escalations list", async () => {
    const escalations = [{ id: "ESC-1", guest_id: "guest-1", reason: "needs manual review" }];
    const fetchMock = vi.fn().mockResolvedValue({ ok: true, json: async () => escalations });
    vi.stubGlobal("fetch", fetchMock);

    const { GET } = await import("./route");
    const response = await GET();
    const body = await response.json();

    expect(body).toEqual(escalations);
    expect(fetchMock).toHaveBeenCalledWith(expect.stringContaining("/host/escalations"));
  });
});
