export interface RosterStudent {
  id: string;
  username: string;
  role: string;
  must_change_pin?: boolean;
}

export interface DeletedUser {
  id: string;
  role: string;
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
