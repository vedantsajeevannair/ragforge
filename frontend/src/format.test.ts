import { formatBytes, formatMs, splitCitations } from "./format";

it("formats bytes", () => {
  expect(formatBytes(512)).toBe("512 B");
  expect(formatBytes(2048)).toBe("2.0 KB");
  expect(formatBytes(15 * 1024 * 1024)).toBe("15 MB");
});

it("formats milliseconds", () => {
  expect(formatMs(12.4)).toBe("12 ms");
  expect(formatMs(2500)).toBe("2.5 s");
});

it("splits citations out of answer text", () => {
  expect(splitCitations("A [1] b [2][3].")).toEqual([
    { kind: "text", text: "A " },
    { kind: "cite", n: 1 },
    { kind: "text", text: " b " },
    { kind: "cite", n: 2 },
    { kind: "cite", n: 3 },
    { kind: "text", text: "." },
  ]);
});
