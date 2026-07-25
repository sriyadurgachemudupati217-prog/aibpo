import { apiClient } from "@/api/client";
import type { TokenPair, User } from "@/types/auth";

export interface RegisterPayload {
  company_name: string;
  full_name: string;
  email: string;
  password: string;
}

export interface LoginPayload {
  email: string;
  password: string;
}

export const authApi = {
  register: (payload: RegisterPayload) =>
    apiClient.post<TokenPair>("/auth/register", payload).then((r) => r.data),

  login: (payload: LoginPayload) =>
    apiClient.post<TokenPair>("/auth/login", payload).then((r) => r.data),

  logout: (refreshToken: string) =>
    apiClient.post("/auth/logout", { refresh_token: refreshToken }).then((r) => r.data),

  me: () => apiClient.get<User>("/auth/me").then((r) => r.data),

  requestPasswordReset: (email: string) =>
    apiClient.post("/auth/password-reset/request", { email }).then((r) => r.data),

  confirmPasswordReset: (token: string, new_password: string) =>
    apiClient
      .post("/auth/password-reset/confirm", { token, new_password })
      .then((r) => r.data),
};
