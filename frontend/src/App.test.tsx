import { render, screen } from "@testing-library/react";
import { App } from "./App";
import { AuthProvider } from "./auth";

afterEach(() => {
  vi.unstubAllGlobals();
  localStorage.clear();
});

it("shows the login page without a token", async () => {
  render(<AuthProvider><App /></AuthProvider>);
  expect(await screen.findByText("Sign in to RAGForge")).toBeInTheDocument();
});

it("hides the admin tab for regular users", async () => {
  localStorage.setItem("ragforge.token", "tok");
  vi.stubGlobal("fetch", vi.fn().mockImplementation((url: string) =>
    Promise.resolve(new Response(JSON.stringify(
      url.endsWith("/auth/me") ? { id: 2, username: "bob", role: "user" } : [])))));
  render(<AuthProvider><App /></AuthProvider>);
  expect(await screen.findByText("bob")).toBeInTheDocument();
  expect(screen.queryByRole("button", { name: "Admin" })).not.toBeInTheDocument();
  expect(screen.getByRole("button", { name: "Ask" })).toHaveAttribute("aria-current", "page");
});
