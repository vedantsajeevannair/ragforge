import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { EditDocument } from "./EditDocument";

const DOC = { doc_id: "a", filename: "guide.md", collection: "ir", doc_type: "markdown",
  size_bytes: 1, chunk_count: 1, title: null, created_at: "", visibility: "shared" as const,
  owner_id: 1 };

afterEach(() => vi.unstubAllGlobals());

it("sends only the changed fields", async () => {
  const fetchMock = vi.fn().mockResolvedValue(
    new Response(JSON.stringify({ ...DOC, collection: "docs" })));
  vi.stubGlobal("fetch", fetchMock);
  const onSaved = vi.fn();
  render(<EditDocument doc={DOC} onSaved={onSaved} onCancel={() => {}} />);
  const input = screen.getByLabelText("Collection");
  await userEvent.clear(input);
  await userEvent.type(input, "docs");
  await userEvent.click(screen.getByRole("button", { name: "Save" }));
  expect(JSON.parse(fetchMock.mock.calls[0][1].body)).toEqual({ collection: "docs" });
  expect(onSaved).toHaveBeenCalledWith(expect.objectContaining({ collection: "docs" }));
});

it("cancels without a request when nothing changed", async () => {
  const fetchMock = vi.fn();
  vi.stubGlobal("fetch", fetchMock);
  const onCancel = vi.fn();
  render(<EditDocument doc={DOC} onSaved={() => {}} onCancel={onCancel} />);
  await userEvent.click(screen.getByRole("button", { name: "Save" }));
  expect(onCancel).toHaveBeenCalled();
  expect(fetchMock).not.toHaveBeenCalled();
});
