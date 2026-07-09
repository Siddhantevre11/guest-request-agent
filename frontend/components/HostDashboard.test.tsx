import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { HostDashboard } from "./HostDashboard";

function mockFetchByUrl(responses: Record<string, unknown>) {
  return vi.fn((url: string) => {
    const key = Object.keys(responses).find((k) => url.includes(k));
    return Promise.resolve({ ok: true, json: async () => responses[key ?? ""] });
  });
}

describe("HostDashboard", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("renders pending approvals and escalations from the backend", async () => {
    vi.stubGlobal(
      "fetch",
      mockFetchByUrl({
        "/host/approvals": [{ id: "APR-1", booking_id: "BK-1001", change: {}, status: "pending" }],
        "/host/escalations": [{ id: "ESC-1", guest_id: "guest-1", reason: "Needs manual review" }],
      }),
    );

    render(<HostDashboard />);

    expect(await screen.findByText("BK-1001")).toBeInTheDocument();
    expect(await screen.findByText("Needs manual review")).toBeInTheDocument();
  });

  it("approving an item calls the decision endpoint and removes it from the queue", async () => {
    const fetchMock = mockFetchByUrl({
      "/host/approvals": [{ id: "APR-1", booking_id: "BK-1001", change: {}, status: "pending" }],
      "/host/escalations": [],
      "/host/decision": { status: "approved", guest_notification: "Great news!", booking: {} },
    });
    vi.stubGlobal("fetch", fetchMock);
    const user = userEvent.setup();

    render(<HostDashboard />);
    await screen.findByText("BK-1001");
    await user.click(screen.getByRole("button", { name: /approve/i }));

    await waitFor(() => expect(screen.queryByText("BK-1001")).not.toBeInTheDocument());
    expect(fetchMock).toHaveBeenCalledWith(
      "/api/host/decision",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ approval_id: "APR-1", decision: "approve" }),
      }),
    );
  });
});
