import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { NavBar } from "./NavBar";

describe("NavBar", () => {
  it("links to both the guest chat and the host dashboard", () => {
    render(<NavBar />);

    expect(screen.getByRole("link", { name: /guest chat/i })).toHaveAttribute("href", "/");
    expect(screen.getByRole("link", { name: /host dashboard/i })).toHaveAttribute("href", "/host");
  });
});
