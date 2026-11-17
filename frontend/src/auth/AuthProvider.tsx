// Who is logged in? The browser can't read the httpOnly cookie, so we ask the server
// (GET /api/auth/me). A 401 simply means "nobody": the query resolves to null.

import { useQuery, useQueryClient } from "@tanstack/react-query";
import { createContext, useCallback, useContext, useMemo, type ReactNode } from "react";
import { ApiError, api } from "../api/client";
import type { LoginInput, RegisterInput, User } from "../api/types";

export const ME_KEY = ["me"] as const;

async function fetchMe(): Promise<User | null> {
  try {
    return await api.me();
  } catch (error) {
    if (error instanceof ApiError && error.status === 401) return null;
    throw error;
  }
}

interface AuthValue {
  user: User | null;
  loading: boolean;
  login: (data: LoginInput) => Promise<void>;
  register: (data: RegisterInput) => Promise<void>;
  logout: () => Promise<void>;
  setUser: (user: User | null) => void;
}

const AuthContext = createContext<AuthValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const queryClient = useQueryClient();
  const { data, isPending } = useQuery({ queryKey: ME_KEY, queryFn: fetchMe, staleTime: 60_000 });

  const setUser = useCallback(
    (user: User | null) => queryClient.setQueryData(ME_KEY, user),
    [queryClient],
  );

  const login = useCallback(
    async (input: LoginInput) => {
      queryClient.removeQueries({ predicate: (q) => q.queryKey[0] !== ME_KEY[0] });
      setUser(await api.login(input));
    },
    [queryClient, setUser],
  );

  const register = useCallback(
    async (input: RegisterInput) => {
      queryClient.removeQueries({ predicate: (q) => q.queryKey[0] !== ME_KEY[0] });
      setUser(await api.register(input));
    },
    [queryClient, setUser],
  );

  const logout = useCallback(async () => {
    await api.logout();
    queryClient.clear(); // drop every cached response that belonged to this user
    setUser(null);
  }, [queryClient, setUser]);

  const value = useMemo<AuthValue>(
    () => ({ user: data ?? null, loading: isPending, login, register, logout, setUser }),
    [data, isPending, login, register, logout, setUser],
  );
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthValue {
  const value = useContext(AuthContext);
  if (!value) throw new Error("useAuth must be used inside AuthProvider");
  return value;
}

/** Same as useAuth().user, but for pages that only render when logged in. */
export function useUser(): User {
  const { user } = useAuth();
  if (!user) throw new Error("useUser called while logged out");
  return user;
}
