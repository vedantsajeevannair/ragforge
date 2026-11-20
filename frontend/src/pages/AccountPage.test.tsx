import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { AuthProvider } from "../auth";
import { AccountPage } from "./AccountPage";

afterEach(() => vi.unstubAllGlobals());

it("rejects mismatched passwords before calling the API", async () => {
  const fetchMock = vi.fn();
  vi.stubGlobal("fetch", fetchMock);
  render(<AuthProvider><AccountPage /></AuthProvider>);
  await userEvent.type(screen.getByLabelText("Current password"), "oldpassword");
  await userEvent.type(screen.getByLabelText("New password"), "newpassword1");
  await userEvent.type(screen.getByLabelText("Confirm new password"), "different12");
  await userEvent.click(screen.getByRole("button", { name: "Update password" }));
  expect(screen.getByRole("status")).toHaveTextContent("do not match");
  expect(fetchMock).not.toHaveBeenCalled();
});
