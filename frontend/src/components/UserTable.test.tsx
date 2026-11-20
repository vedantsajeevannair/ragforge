import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { UserTable } from "./UserTable";

afterEach(() => vi.unstubAllGlobals());

const json = (body: unknown, status = 200) =>
  new Response(status === 204 ? null : JSON.stringify(body), { status });

it("promotes a user and blocks deleting yourself", async () => {
  const fetchMock = vi.fn()
    .mockResolvedValueOnce(json([{ id: 1, username: "admin", role: "admin" },
      { id: 2, username: "bob", role: "user" }]))
    .mockResolvedValueOnce(json({ id: 2, username: "bob", role: "admin" }));
  vi.stubGlobal("fetch", fetchMock);
  render(<UserTable currentUserId={1} />);
  expect(await screen.findByText("bob")).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "Delete user admin" })).toBeDisabled();
  await userEvent.click(screen.getByRole("button", { name: "Make admin" }));
  expect(fetchMock.mock.calls[1][1].method).toBe("PATCH");
  expect(await screen.findAllByText("admin")).toHaveLength(3);
});

it("shows the last-admin conflict", async () => {
  vi.stubGlobal("fetch", vi.fn()
    .mockResolvedValueOnce(json([{ id: 1, username: "root", role: "admin" }]))
    .mockResolvedValueOnce(json({ detail: "cannot remove the last admin" }, 409)));
  render(<UserTable currentUserId={1} />);
  await userEvent.click(await screen.findByRole("button", { name: "Make user" }));
  expect(await screen.findByRole("alert")).toHaveTextContent("last admin");
});
