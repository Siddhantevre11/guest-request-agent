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

  it("shows the guest's actual message and the proposed change details, not just the booking id", async () => {
    vi.stubGlobal(
      "fetch",
      mockFetchByUrl({
        "/host/approvals": [
          {
            id: "APR-1",
            booking_id: "BK-1001",
            guest_message: "can I check out at 1pm instead of 11am on my last day?",
            change: { new_checkout_time: "13:00", fee: 25, date: "2026-08-05" },
            status: "pending",
          },
        ],
        "/host/escalations": [],
      }),
    );

    render(<HostDashboard />);

    expect(await screen.findByText(/can i check out at 1pm instead of 11am on my last day/i)).toBeInTheDocument();
    expect(screen.getByText(/13:00/)).toBeInTheDocument();
    expect(screen.getByText(/25/)).toBeInTheDocument();
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
