import { AxiosError } from "axios";
import { describe, expect, it } from "vitest";

import { apiErrorMessage } from "@/lib/api";

describe("apiErrorMessage", () => {
  it("returns the string detail from an axios error", () => {
    const err = new AxiosError("Request failed");
    err.response = { data: { detail: "Email already registered" } } as never;
    expect(apiErrorMessage(err)).toBe("Email already registered");
  });

  it("returns the first message from a validation-error array", () => {
    const err = new AxiosError("Request failed");
    err.response = { data: { detail: [{ msg: "field required" }] } } as never;
    expect(apiErrorMessage(err)).toBe("field required");
  });

  it("falls back to the provided default for non-axios errors", () => {
    expect(apiErrorMessage(new Error("boom"), "Oops")).toBe("Oops");
  });

  it("uses the generic default when none is provided", () => {
    expect(apiErrorMessage(null)).toBe("Something went wrong");
  });
});
