import { applyTheme, loadTheme, nextTheme } from "./theme";

afterEach(() => localStorage.clear());

it("cycles system -> dark -> light -> system", () => {
  expect(nextTheme("system")).toBe("dark");
  expect(nextTheme("dark")).toBe("light");
  expect(nextTheme("light")).toBe("system");
});

it("persists explicit themes and clears for system", () => {
  applyTheme("dark");
  expect(document.documentElement.dataset.theme).toBe("dark");
  expect(loadTheme()).toBe("dark");
  applyTheme("system");
  expect(document.documentElement.hasAttribute("data-theme")).toBe(false);
  expect(loadTheme()).toBe("system");
});
