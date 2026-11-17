import { afterEach, describe, expect, it, vi } from "vitest";
import { ApiError, api, toQueryString } from "./client";

function mockFetch(status: number, body: unknown): ReturnType<typeof vi.fn> {
  const fn = vi
    .fn()
    .mockResolvedValue(new Response(status === 204 ? null : JSON.stringify(body), { status }));
  vi.stubGlobal("fetch", fn);
  return fn;
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("api client", () => {
  it("sends credentials so the httpOnly cookie travels with every request", async () => {
    const fetchMock = mockFetch(200, { status: "ok", database: "ok" });
    await api.health();
    expect(fetchMock).toHaveBeenCalledWith(
      "/api/health",
      expect.objectContaining({ credentials: "include" }),
    );
  });

  it("throws ApiError with the backend's string detail", async () => {
    mockFetch(404, { detail: "Todo not found." });
    await expect(api.me()).rejects.toEqual(new ApiError(404, "Todo not found."));
  });

  it("turns a 422 validation list into a readable message", async () => {
    mockFetch(422, {
      detail: [{ loc: ["body", "amount"], msg: "Input should be greater than 0" }],
    });
    await expect(api.me()).rejects.toThrow("amount: Input should be greater than 0");
  });

  it("returns undefined for 204 No Content", async () => {
    mockFetch(204, null);
    await expect(api.deleteTodo(1)).resolves.toBeUndefined();
  });

  it("serialises filters and skips empty ones", async () => {
    const fetchMock = mockFetch(200, { items: [], total: 0, limit: 50, offset: 0 });
    await api.listTodos({ priority: "high", q: "", completed: false, limit: 10 });
    expect(fetchMock.mock.calls[0]?.[0]).toBe("/api/todos?priority=high&completed=false&limit=10");
  });
});

describe("toQueryString", () => {
  it("returns an empty string when nothing is set", () => {
    expect(toQueryString({ a: undefined, b: null, c: "" })).toBe("");
  });
});
