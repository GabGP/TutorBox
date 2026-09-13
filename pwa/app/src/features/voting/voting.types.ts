export type OptionLetter = 'A' | 'B' | 'C' | 'D';

export interface VotePayload {
  selected_option: OptionLetter;
  transport_type: 'web';
  response_time_ms: number;
}

export interface VoteResponse {
  vote_id: string;
  round_id: string;
  selected_option: OptionLetter;
  recorded_at: string;
}
