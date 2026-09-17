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

export interface TTSStatusResponse {
  engine: string;
  loaded: boolean;
  model_id: string;
}

export interface TTSLoadRequest {
  engine?: string | null;
  lang?: SpeechLanguage;
  voice?: string | null;
}

export interface TTSLoadResponse {
  engine: string;
  loaded: boolean;
  model_id: string;
  load_ms: number;
}

export interface TTSUnloadRequest {
  engine?: string | null;
}

export interface TTSUnloadResponse {
  engine: string;
  loaded: boolean;
}

export interface TTSVoiceItem {
  id: string;
  lang: string;
  engine: string;
}
