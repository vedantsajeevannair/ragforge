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

describe("waitForJob", () => {
  afterEach(() => vi.unstubAllGlobals());

  it("polls until the job is done", async () => {
    const { waitForJob } = await import("./api");
    const states = [
      { id: 1, kind: "upload", status: "queued", result: null, error: null },
      { id: 1, kind: "upload", status: "done", result: { doc_id: "x" }, error: null },
    ];
    const fetchMock = vi.fn().mockImplementation(() =>
      Promise.resolve(new Response(JSON.stringify(states.shift()))));
    vi.stubGlobal("fetch", fetchMock);
    const sleeps: number[] = [];
    const result = await waitForJob(1, async (ms) => { sleeps.push(ms); });
    expect(result).toEqual({ doc_id: "x" });
    expect(sleeps).toEqual([250]);
  });

  it("throws the job error", async () => {
    const { waitForJob } = await import("./api");
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(JSON.stringify(
      { id: 1, kind: "upload", status: "failed", result: null, error: "no text" }))));
    await expect(waitForJob(1, async () => {})).rejects.toThrow("no text");
  });
});
