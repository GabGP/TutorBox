import type { UserRole } from '../auth/auth.types';

export interface RosterStudent {
  id: string;
  username: string;
  role: UserRole;
  must_change_pin?: boolean;
}

export interface DeletedUser {
  id: string;
  role: UserRole;
  former_username: string;
  deleted_at: string;
}

export interface ResetPinResponse {
  temporary_pin: string;
}

export interface RecoverUserResponse {
  username: string;
  temporary_pin: string;
}
