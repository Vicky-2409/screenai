import { render } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { HtmlContent } from "@/components/RichTextEditor";

describe("HtmlContent", () => {
  it("renders allowed formatting tags", () => {
    const { container } = render(<HtmlContent html="<p>Hello <b>world</b></p>" />);
    expect(container.querySelector("b")?.textContent).toBe("world");
  });

  it("strips dangerous script tags (XSS protection)", () => {
    const { container } = render(
      <HtmlContent html={'<p>safe</p><script>window.__x=1</script>'} />,
    );
    expect(container.querySelector("script")).toBeNull();
    expect(container.textContent).toContain("safe");
  });

  it("renders nothing for empty html", () => {
    const { container } = render(<HtmlContent html="" />);
    expect(container.firstChild).toBeNull();
  });
});
