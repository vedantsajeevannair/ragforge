import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { CopyButton } from "./CopyButton";

it("copies text and confirms", async () => {
  const user = userEvent.setup();
  render(<CopyButton text="answer [1]" />);
  await user.click(screen.getByRole("button", { name: "Copy answer" }));
  expect(await navigator.clipboard.readText()).toBe("answer [1]");
  expect(screen.getByRole("button")).toHaveTextContent("Copied");
});
