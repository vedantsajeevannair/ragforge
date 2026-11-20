import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { CollectionTable } from "./CollectionTable";

afterEach(() => vi.unstubAllGlobals());

it("deletes a collection after confirmation", async () => {
  const fetchMock = vi.fn()
    .mockResolvedValueOnce(new Response(JSON.stringify([{ name: "hr", documents: 3, chunks: 12 }])))
    .mockResolvedValueOnce(new Response(JSON.stringify({ deleted: 3 })));
  vi.stubGlobal("fetch", fetchMock);
  vi.spyOn(window, "confirm").mockReturnValue(true);
  render(<CollectionTable />);
  await userEvent.click(await screen.findByRole("button", { name: "Delete collection hr" }));
  expect(screen.queryByText("12")).toBeNull();
  expect(fetchMock.mock.calls[1][0]).toBe("/api/documents/collections/hr");
  expect(await screen.findByText("No collections yet.")).toBeInTheDocument();
});
