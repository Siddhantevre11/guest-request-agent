import { act, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { ChatWindow } from "./ChatWindow";

describe("ChatWindow notification polling", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.unstubAllGlobals();
  });

  it("polls for host notifications and displays them as agent messages", async () => {
    const fetchMock = vi.fn((url: string) => {
      if (url.includes("/api/notifications")) {
        return Promise.resolve({
          ok: true,
          json: async () => [{ id: "NOTIF-1", text: "Great news — your checkout has been extended to 13:00." }],
        });
      }
      return Promise.resolve({ ok: true, json: async () => ({ reply: "" }) });
    });
    vi.stubGlobal("fetch", fetchMock);

    render(<ChatWindow />);

    await act(async () => {
      await vi.advanceTimersByTimeAsync(5000);
    });

    expect(screen.getByText("Great news — your checkout has been extended to 13:00.")).toBeInTheDocument();
  });
});
