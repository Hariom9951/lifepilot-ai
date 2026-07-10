export interface Role {
  id: string;
  name: string;
  description: string | null;
  permissions: string[] | Record<string, unknown>;
}

export interface User {
  id: string;
  full_name: string;
  username: string;
  email: string;
  avatar_url: string | null;
  timezone: string;
  language: string;
  is_active: boolean;
  is_verified: boolean;
  role: Role;
  created_at: string;
  updated_at: string;
  last_login: string | null;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  user: User;
}
