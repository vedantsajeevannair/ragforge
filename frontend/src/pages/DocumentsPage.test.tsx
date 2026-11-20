import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { DocumentsPage } from "./DocumentsPage";

const DOCS = [
  { doc_id: "a", filename: "guide.md", collection: "ir", doc_type: "markdown",
    size_bytes: 2048, chunk_count: 4, title: null, created_at: "2026-11-20 10:00:00",
    visibility: "private", owner_id: 1 },
  { doc_id: "b", filename: "bread.txt", collection: "food", doc_type: "text",
    size_bytes: 100, chunk_count: 1, title: null, created_at: "2026-11-20 10:00:00",
    visibility: "shared", owner_id: 1 },
];

function json(body: unknown, status = 200) {
  return new Response(status === 204 ? null : JSON.stringify(body), {
    status, headers: { "Content-Type": "application/json" } });
}

afterEach(() => vi.unstubAllGlobals());

it("lists, filters and deletes documents", async () => {
  const fetchMock = vi.fn()
    .mockResolvedValueOnce(json(DOCS))
    .mockResolvedValueOnce(json(null, 204));
  vi.stubGlobal("fetch", fetchMock);
  vi.spyOn(window, "confirm").mockReturnValue(true);

  render(<DocumentsPage />);
  expect(await screen.findByText("guide.md")).toBeInTheDocument();
  expect(screen.getByText("2.0 KB")).toBeInTheDocument();
  expect(screen.getByText("private")).toBeInTheDocument();

  await userEvent.type(screen.getByLabelText("Filter documents"), "food");
  expect(screen.queryByText("guide.md")).not.toBeInTheDocument();
  expect(screen.getByText("1 of 2")).toBeInTheDocument();

  await userEvent.click(screen.getByRole("button", { name: "Delete bread.txt" }));
  expect(fetchMock.mock.calls[1][0]).toBe("/api/documents/b");
  expect(screen.queryByText("bread.txt")).not.toBeInTheDocument();
});

it("shows an empty state", async () => {
  vi.stubGlobal("fetch", vi.fn().mockResolvedValueOnce(json([])));
  render(<DocumentsPage />);
  expect(await screen.findByText(/No documents yet/)).toBeInTheDocument();
});
