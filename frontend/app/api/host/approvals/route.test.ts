import { afterEach, describe, expect, it, vi } from "vitest";

describe("GET /api/host/approvals", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("returns the backend's pending approvals list", async () => {
    const approvals = [{ id: "APR-1", booking_id: "BK-1001", change: {}, status: "pending" }];
    const fetchMock = vi.fn().mockResolvedValue({ ok: true, json: async () => approvals });
    vi.stubGlobal("fetch", fetchMock);

    const { GET } = await import("./route");
    const response = await GET();
    const body = await response.json();

    expect(body).toEqual(approvals);
    expect(fetchMock).toHaveBeenCalledWith(expect.stringContaining("/host/approvals"));
  });
});
