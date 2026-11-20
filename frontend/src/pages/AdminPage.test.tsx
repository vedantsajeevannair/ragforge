import { render, screen } from "@testing-library/react";
import { AdminPage } from "./AdminPage";

afterEach(() => vi.unstubAllGlobals());

it("renders stat tiles", async () => {
  const stats = { documents: 9, chunks: 33, collections: 2, users: 3, queries: 10,
    grounded_rate: 0.8, avg_retrieval_ms: 4.2, avg_generation_ms: 1500, thumbs_up: 3,
    thumbs_down: 1 };
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(JSON.stringify(stats))));
  render(<AdminPage />);
  expect(await screen.findByText("80%")).toBeInTheDocument();
  expect(screen.getByText("1.5 s")).toBeInTheDocument();
  expect(screen.getByText("75% of 4")).toBeInTheDocument();
});

it("shows forbidden error for non-admins", async () => {
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue(
    new Response(JSON.stringify({ detail: "admin role required" }), { status: 403 })));
  render(<AdminPage />);
  expect(await screen.findByRole("alert")).toHaveTextContent("admin role required");
});
