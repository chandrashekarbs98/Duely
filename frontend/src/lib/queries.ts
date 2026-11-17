// Shared React Query helpers.
//
// After any change (create, toggle, pay, delete…) many screens can be stale: the list,
// Home, Reminders, Stats. Invalidating every data query (but not "me") is simple and
// always correct; React Query refetches only what is currently on screen.

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { ME_KEY } from "../auth/AuthProvider";

export function useInvalidateData() {
  const queryClient = useQueryClient();
  return () => queryClient.invalidateQueries({ predicate: (q) => q.queryKey[0] !== ME_KEY[0] });
}

/** A mutation that refreshes all data queries when it succeeds. */
export function useDataMutation<TArgs, TResult>(fn: (args: TArgs) => Promise<TResult>) {
  const invalidate = useInvalidateData();
  return useMutation({ mutationFn: fn, onSuccess: () => invalidate() });
}
