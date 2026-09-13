export interface RosterStudent {
  id: string;
  username: string;
  role: string;
  must_change_pin?: boolean;
}

export interface ResetPinResponse {
  temporary_pin: string;
}
