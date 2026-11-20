import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { useState } from "react";
import { ErrorBoundary } from "./ErrorBoundary";

let shouldThrow = true;

function Bomb() {
  const [n] = useState(0);
  if (shouldThrow) throw new Error("boom");
  return <p>recovered {n}</p>;
}

it("shows a fallback and recovers on retry", async () => {
  vi.spyOn(console, "error").mockImplementation(() => {});
  render(<ErrorBoundary><Bomb /></ErrorBoundary>);
  expect(screen.getByRole("alert")).toHaveTextContent("boom");
  shouldThrow = false;
  await userEvent.click(screen.getByRole("button", { name: "Try again" }));
  expect(screen.getByText("recovered 0")).toBeInTheDocument();
});
