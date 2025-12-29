import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

// Mock the auth service so the page renders without any network calls.
vi.mock("@/services/auth", () => ({
  login: vi.fn(),
  register: vi.fn(),
  fetchMe: vi.fn(),
  forgotPassword: vi.fn(),
  resetPassword: vi.fn(),
}));

import { AuthProvider } from "@/context/AuthContext";
import { LoginPage } from "@/pages/LoginPage";

function renderWithProviders(ui: React.ReactElement) {
  return render(
    <MemoryRouter>
      <AuthProvider>{ui}</AuthProvider>
    </MemoryRouter>,
  );
}

describe("LoginPage", () => {
  it("renders the sign-in form with email, password and helper links", () => {
    renderWithProviders(<LoginPage />);
    expect(screen.getByRole("heading", { name: /sign in/i })).toBeInTheDocument();
    expect(screen.getByText(/forgot password\?/i)).toBeInTheDocument();
    expect(screen.getByText(/create one/i)).toBeInTheDocument();
  });
});
