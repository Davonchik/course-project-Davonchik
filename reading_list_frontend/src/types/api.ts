// API Types based on OpenAPI schema

export type EntryKind = 'book' | 'article';

export type EntryStatus = 'planned' | 'in_progress' | 'finished';

export interface RegisterIn {
  email: string;
  password: string;
  device_id?: string | null;
}

export interface LoginIn {
  username: string;
  password: string;
  grant_type?: string | null;
  scope?: string;
  client_id?: string | null;
  client_secret?: string | null;
}

export interface RefreshIn {
  refresh_token: string;
}

export interface TokenOut {
  access_token: string;
  refresh_token: string;
  token_type?: string;
  device_id: string;
}

export interface LogoutIn {
  device_id: string;
  refresh_token?: string | null;
}

export interface EntryCreate {
  title: string;
  kind: EntryKind;
  link?: string | null;
  status?: EntryStatus;
}

export interface EntryUpdate {
  title?: string | null;
  kind?: EntryKind | null;
  link?: string | null;
  status?: EntryStatus | null;
}

export interface Entry {
  id: number;
  title: string;
  kind: EntryKind;
  link?: string | null;
  status: EntryStatus;
  owner_id: number;
}

export interface User {
  id: number;
  email: string;
  role: 'admin' | 'user';
}

export interface UserListItem {
  id: number;
  email: string;
}

export interface ValidationError {
  loc: (string | number)[];
  msg: string;
  type: string;
}

export interface HTTPValidationError {
  detail: ValidationError[];
}

export interface ListEntriesParams {
  entry_status?: EntryStatus | null;
  limit?: number;
  offset?: number;
  owner_id?: number | null; // Admin only
}

export interface ListEntriesResponse {
  items: Entry[];
  total: number;
  limit: number;
  offset: number;
}
