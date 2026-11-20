import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { AnswerView } from "./AnswerView";

const citations = [
  { number: 1, chunk_id: "d:0", doc_id: "d", source: "guide.md", snippet: "RRF merges lists" },
];

it("renders citation chips and highlights the source when clicked", async () => {
  render(<AnswerView answer="RRF merges ranked lists [1]." citations={citations} />);
  expect(screen.getByText("[1] guide.md")).toBeInTheDocument();
  await userEvent.click(screen.getByRole("button", { name: "Show source 1" }));
  expect(screen.getByTestId("source-1")).toHaveClass("active");
});

it("shows a cursor while streaming", () => {
  render(<AnswerView answer="Partial" citations={[]} streaming />);
  expect(screen.getByText("▍")).toBeInTheDocument();
});
