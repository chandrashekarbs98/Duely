import { QueryClient } from "@tanstack/react-query";
import { describe, expect, it } from "vitest";
import { ME_KEY, forgetUser } from "./session";

describe("forgetUser", () => {
  it("keeps the 'me' entry as null and drops the user's data", () => {
    const client = new QueryClient();
    client.setQueryData(ME_KEY, { id: 1, name: "Alice" });
    client.setQueryData(["home"], { urgent: [] });
    client.setQueryData(["todos", { page: 1 }], { items: [] });

    forgetUser(client);

    // "me" must still exist (as null) so the auth observer sees the change and redirects.
    expect(client.getQueryCache().find({ queryKey: ME_KEY })).toBeDefined();
    expect(client.getQueryData(ME_KEY)).toBeNull();
    expect(client.getQueryData(["home"])).toBeUndefined();
    expect(client.getQueryData(["todos", { page: 1 }])).toBeUndefined();
  });
});
