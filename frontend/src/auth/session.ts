// What happens to the React Query cache when the user logs out.

import type { QueryClient } from "@tanstack/react-query";

export const ME_KEY = ["me"] as const;

/**
 * Forget the logged-in user and everything cached for them.
 *
 * Order matters. First set "me" to null: RequireAuth then swaps the private pages for a
 * redirect to /login, so nothing is left on screen asking for data. Then drop the rest of
 * the cache, but keep the "me" entry. (Calling queryClient.clear() removed "me" too, so the
 * still-mounted page refetched without a cookie and showed "Not authenticated.")
 */
export function forgetUser(queryClient: QueryClient): void {
  queryClient.setQueryData(ME_KEY, null);
  queryClient.removeQueries({ predicate: (q) => q.queryKey[0] !== ME_KEY[0] });
}
