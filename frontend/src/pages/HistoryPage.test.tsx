import { historyToCsv } from "./HistoryPage";

it("exports history as escaped CSV", () => {
  const csv = historyToCsv([{
    id: 1, question: 'What is "RRF"?', answer: "Fusion, of ranks [1]", grounded: true,
    mode: "hybrid", feedback: 1, created_at: "2026-11-20 10:00:00",
    citations: [{ number: 1, chunk_id: "c", doc_id: "d", source: "a.md", snippet: "" }],
  }]);
  const [header, row] = csv.split("\n");
  expect(header).toBe("id,created_at,mode,grounded,feedback,question,answer,sources");
  expect(row).toBe('1,2026-11-20 10:00:00,hybrid,true,1,"What is ""RRF""?",' +
    '"Fusion, of ranks [1]",a.md');
});

import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { HistoryPage } from "./HistoryPage";

const item = (id: number) => ({ id, question: `q${id}`, answer: "a", grounded: true,
  mode: "hybrid", citations: [], feedback: null, created_at: "2026-11-20 10:00:00" });

afterEach(() => vi.unstubAllGlobals());

it("loads older pages until a short page arrives", async () => {
  const first = Array.from({ length: 20 }, (_, i) => item(40 - i));
  const fetchMock = vi.fn()
    .mockResolvedValueOnce(new Response(JSON.stringify(first)))
    .mockResolvedValueOnce(new Response(JSON.stringify([item(3)])));
  vi.stubGlobal("fetch", fetchMock);
  render(<HistoryPage />);
  await userEvent.click(await screen.findByRole("button", { name: "Load older questions" }));
  expect(fetchMock.mock.calls[1][0]).toBe("/api/history?limit=20&before_id=21");
  expect(await screen.findByText("q3")).toBeInTheDocument();
  expect(screen.queryByRole("button", { name: "Load older questions" })).toBeNull();
});
