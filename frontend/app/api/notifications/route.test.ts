import { afterEach, describe, expect, it, vi } from "vitest";

describe("GET /api/notifications", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("forwards guest_id and conversation_id to the backend and returns its notifications", async () => {
    const notifications = [{ id: "NOTIF-1", text: "Great news — your checkout has been extended to 13:00." }];
    const fetchMock = vi.fn().mockResolvedValue({ ok: true, json: async () => notifications });
    vi.stubGlobal("fetch", fetchMock);

    const { GET } = await import("./route");
    const request = new Request("http://localhost/api/notifications?guest_id=guest-1&conversation_id=conv-1");

    const response = await GET(request);
    const body = await response.json();

    expect(body).toEqual(notifications);
    const calledUrl = fetchMock.mock.calls[0][0] as string;
    expect(calledUrl).toContain("/notifications");
    expect(calledUrl).toContain("guest_id=guest-1");
    expect(calledUrl).toContain("conversation_id=conv-1");
  });
});
