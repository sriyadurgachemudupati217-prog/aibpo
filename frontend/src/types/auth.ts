export type UserRole = "admin" | "manager" | "employee";

export interface User {
  id: string;
  company_id: string;
  email: string;
  full_name: string;
  role: UserRole;
  is_active: boolean;
}

export interface TokenPair {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface ApiError {
  detail: string | { msg: string; loc: (string | number)[] }[];
}
