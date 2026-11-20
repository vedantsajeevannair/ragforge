import { parseSSE } from "./api";

describe("parseSSE", () => {
  it("parses complete events and keeps the partial remainder", () => {
    const buf =
      'event: token\ndata: {"text":"Hel"}\n\n' +
      'event: token\ndata: {"text":"lo"}\n\n' +
      "event: done\ndata: {";
    const { events, rest } = parseSSE(buf);
    expect(events).toEqual([
      { event: "token", data: { text: "Hel" } },
      { event: "token", data: { text: "lo" } },
    ]);
    expect(rest).toBe("event: done\ndata: {");
  });

  it("ignores blocks without data", () => {
    expect(parseSSE("event: ping\n\n").events).toEqual([]);
  });
});
