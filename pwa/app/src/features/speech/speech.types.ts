export type SpeechLanguage = 'es' | 'quc';

export type SpeechState =
  | 'idle'
  | 'loading'
  | 'playing'
  | 'done'
  | 'error'
  | 'blocked';

export interface SpeechInfo {
  state: SpeechState;
  msg: string;
  roundIndex: number;
}
