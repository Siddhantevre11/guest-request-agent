import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { ChatWindow } from "./ChatWindow";

describe("ChatWindow", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("sends the guest's message and displays the agent's reply", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ reply: "The wifi password is SunnyDays2024!." }),
    });
    vi.stubGlobal("fetch", fetchMock);
    const user = userEvent.setup();

    render(<ChatWindow />);

    await user.type(screen.getByLabelText(/message/i), "what's the wifi password?");
    await user.click(screen.getByRole("button", { name: /send/i }));

    expect(await screen.findByText("The wifi password is SunnyDays2024!.")).toBeInTheDocument();
    expect(screen.getByText("what's the wifi password?")).toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledWith(
      "/api/message",
      expect.objectContaining({
        method: "POST",
        body: expect.stringContaining("what's the wifi password?"),
      }),
    );
  });
});
