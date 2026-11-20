import { act, render, screen } from "@testing-library/react";
import { ToastProvider, useToast } from "./Toasts";

function Trigger() {
  const toast = useToast();
  return <button type="button" onClick={() => toast("Saved")}>go</button>;
}

it("shows and auto-dismisses a toast", () => {
  vi.useFakeTimers();
  render(<ToastProvider timeoutMs={1000}><Trigger /></ToastProvider>);
  act(() => screen.getByRole("button").click());
  expect(screen.getByRole("status")).toHaveTextContent("Saved");
  act(() => vi.advanceTimersByTime(1001));
  expect(screen.queryByRole("status")).toBeNull();
  vi.useRealTimers();
});
