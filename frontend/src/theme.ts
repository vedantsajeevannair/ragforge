export type Theme = "system" | "light" | "dark";

const KEY = "ragforge.theme";

export function loadTheme(): Theme {
  const v = localStorage.getItem(KEY);
  return v === "light" || v === "dark" ? v : "system";
}

export function applyTheme(theme: Theme): void {
  const root = document.documentElement;
  if (theme === "system") {
    root.removeAttribute("data-theme");
    localStorage.removeItem(KEY);
  } else {
    root.setAttribute("data-theme", theme);
    localStorage.setItem(KEY, theme);
  }
}

export function nextTheme(theme: Theme): Theme {
  return theme === "system" ? "dark" : theme === "dark" ? "light" : "system";
}
