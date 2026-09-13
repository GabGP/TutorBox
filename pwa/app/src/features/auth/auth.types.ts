export type UserRole = 'student' | 'teacher' | 'admin';

export interface User {
  id: string;
  username: string;
  role: UserRole;
}

export interface LoginResponse {
  session_id: string;
  must_change_pin?: boolean;
}

export interface SignupResponse {
  id: string;
  username: string;
  role: string;
}

export interface PinChangePayload {
  current_pin: string;
  new_pin: string;
}
