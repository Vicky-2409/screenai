import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { ScoreBadge, StatusBadge } from "@/components/ui";

describe("UI primitives", () => {
  it("renders a score badge with rounded percentage", () => {
    render(<ScoreBadge score={87.6} />);
    expect(screen.getByText("88%")).toBeInTheDocument();
  });

  it("renders a humanized status badge", () => {
    render(<StatusBadge status="shortlisted" />);
    expect(screen.getByText("shortlisted")).toBeInTheDocument();
  });
});
