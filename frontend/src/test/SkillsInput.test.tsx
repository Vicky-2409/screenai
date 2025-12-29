import { fireEvent, render, screen } from "@testing-library/react";
import { useState } from "react";
import { describe, expect, it } from "vitest";

import { SkillsInput } from "@/components/SkillsInput";

function Harness({ initial = [] as string[] }) {
  const [skills, setSkills] = useState<string[]>(initial);
  return <SkillsInput value={skills} onChange={setSkills} />;
}

describe("SkillsInput", () => {
  it("adds a normalized (lowercased) skill on Enter", () => {
    render(<Harness />);
    const input = screen.getByPlaceholderText(/type a skill/i);
    fireEvent.change(input, { target: { value: "Python" } });
    fireEvent.keyDown(input, { key: "Enter" });
    expect(screen.getByText("python")).toBeInTheDocument();
  });

  it("does not add duplicate skills", () => {
    render(<Harness initial={["python"]} />);
    const input = screen.getByPlaceholderText(/type a skill/i);
    fireEvent.change(input, { target: { value: "python" } });
    fireEvent.keyDown(input, { key: "Enter" });
    expect(screen.getAllByText("python")).toHaveLength(1);
  });

  it("removes a skill when its remove button is clicked", () => {
    render(<Harness initial={["react", "docker"]} />);
    const reactChip = screen.getByText("react");
    const button = reactChip.querySelector("button")!;
    fireEvent.click(button);
    expect(screen.queryByText("react")).not.toBeInTheDocument();
    expect(screen.getByText("docker")).toBeInTheDocument();
  });
});
