import { render } from "@testing-library/react";
import { Highlighted } from "./Highlighted";

it("wraps spans in mark elements", () => {
  const { container } = render(<Highlighted text="rank the documents" spans={[[9, 18], [0, 4]]} />);
  const marks = [...container.querySelectorAll("mark")].map((m) => m.textContent);
  expect(marks).toEqual(["rank", "documents"]);
  expect(container.textContent).toBe("rank the documents");
});

it("truncates and ignores spans past the limit", () => {
  const { container } = render(
    <Highlighted text="alpha beta gamma" spans={[[11, 16]]} maxLength={10} />);
  expect(container.querySelector("mark")).toBeNull();
  expect(container.textContent).toBe("alpha beta…");
});
