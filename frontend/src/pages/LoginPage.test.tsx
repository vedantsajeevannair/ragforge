import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { AuthProvider } from "../auth";
import { LoginPage } from "./LoginPage";

function mockFetch(responses: Array<{ status: number; body: unknown }>) {
  const fn = vi.fn();
  for (const r of responses) {
    fn.mockResolvedValueOnce(
      new Response(JSON.stringify(r.body), {
        status: r.status,
        headers: { "Content-Type": "application/json" },
      }),
    );
  }
  vi.stubGlobal("fetch", fn);
  return fn;
}

afterEach(() => {
  vi.unstubAllGlobals();
  localStorage.clear();
});

it("shows the server error on failed login", async () => {
  mockFetch([{ status: 401, body: { detail: "invalid username or password" } }]);
  render(<AuthProvider><LoginPage /></AuthProvider>);
  await userEvent.type(screen.getByLabelText("Username"), "alice");
  await userEvent.type(screen.getByLabelText("Password"), "password123");
  await userEvent.click(screen.getByRole("button", { name: "Sign in" }));
  expect(await screen.findByRole("alert")).toHaveTextContent("invalid username or password");
});

it("stores the token after registering", async () => {
  const fetchMock = mockFetch([
    { status: 201, body: { access_token: "tok", token_type: "bearer", role: "admin" } },
    { status: 200, body: { id: 1, username: "alice", role: "admin" } },
  ]);
  render(<AuthProvider><LoginPage /></AuthProvider>);
  await userEvent.click(screen.getByRole("button", { name: "Create one" }));
  await userEvent.type(screen.getByLabelText("Username"), "alice");
  await userEvent.type(screen.getByLabelText("Password"), "password123");
  await userEvent.click(screen.getByRole("button", { name: "Create account" }));
  await vi.waitFor(() => expect(localStorage.getItem("ragforge.token")).toBe("tok"));
  expect(fetchMock.mock.calls[0][0]).toBe("/api/auth/register");
});
