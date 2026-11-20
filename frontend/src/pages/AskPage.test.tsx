import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { AskPage } from "./AskPage";

afterEach(() => vi.unstubAllGlobals());

function sse(answer: string, id: number) {
  const body =
    `event: sources\ndata: {"hits": []}\n\n` +
    `event: token\ndata: ${JSON.stringify({ text: answer })}\n\n` +
    `event: done\ndata: ${JSON.stringify({ query_id: id, answer, grounded: true, confidence: 0.8,
      citations: [], timings_ms: { retrieval: 2, generation: 1 } })}\n\n`;
  return new Response(body, { headers: { "Content-Type": "text/event-stream" } });
}

it("streams an answer and sends earlier questions on follow-ups", async () => {
  const fetchMock = vi.fn().mockImplementation((url: string) =>
    url.endsWith("/collections")
      ? Promise.resolve(new Response("[]"))
      : Promise.resolve(sse(fetchMock.mock.calls.length > 2 ? "Second." : "First.", 1)));
  vi.stubGlobal("fetch", fetchMock);
  render(<AskPage />);

  await userEvent.type(screen.getByLabelText("Question"), "How does BM25 work?");
  await userEvent.click(screen.getByRole("button", { name: "Ask" }));
  expect(await screen.findByText("First.")).toBeInTheDocument();
  expect(screen.getByText("Grounded in sources")).toBeInTheDocument();
  expect(screen.getByText("Confidence: high")).toBeInTheDocument();

  await userEvent.type(screen.getByLabelText("Question"), "What about its parameters?");
  await userEvent.click(screen.getByRole("button", { name: "Ask" }));
  expect(await screen.findByText("Second.")).toBeInTheDocument();
  const askCalls = fetchMock.mock.calls.filter(([u]) => String(u).endsWith("/ask/stream"));
  const body = JSON.parse(askCalls[1][1].body);
  expect(body.previous_questions).toEqual(["How does BM25 work?"]);
  expect(screen.getByText("How does BM25 work?")).toBeInTheDocument();
});


it("focuses the question box when / is pressed", async () => {
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response("[]")));
  render(<AskPage />);
  await userEvent.keyboard("/");
  expect(screen.getByLabelText("Question")).toHaveFocus();
});
