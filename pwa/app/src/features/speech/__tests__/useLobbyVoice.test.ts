import { act, renderHook } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { ttsApi } from '../speechApi';
import { VOICE_LOAD_FAILED, VOICE_UNLOAD_FAILED, VOICE_UNLOADED, useLobbyVoice, voiceName } from '../useLobbyVoice';

vi.mock('../speechApi', () => ({
  ttsApi: { getStatus: vi.fn(), load: vi.fn(), unload: vi.fn() },
}));

function sink() {
  return { pushToast: vi.fn((_toast: unknown) => 'toast-1'), dismissToast: vi.fn() };
}

function messages(notices: ReturnType<typeof sink>): unknown[] {
  return notices.pushToast.mock.calls.map(([toast]) => toast);
}

describe('useLobbyVoice', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
  });

  it('loads the saved voice with a sticky toast, then says how long it took', async () => {
    localStorage.setItem('tb_voice', JSON.stringify({ lang: 'es', engine: 'qwen3-tts', voice: 'voz-x' }));
    vi.mocked(ttsApi.getStatus).mockResolvedValue({ engine: 'qwen3-tts', loaded: false, model_id: '' });
    vi.mocked(ttsApi.load).mockResolvedValue({ engine: 'qwen3-tts', loaded: true, model_id: 'q', load_ms: 7000 });
    const notices = sink();
    const { result } = renderHook(() => useLobbyVoice(notices));

    await act(() => result.current.prepare('es'));

    expect(ttsApi.getStatus).toHaveBeenCalledWith('qwen3-tts', 'es');
    expect(ttsApi.load).toHaveBeenCalledWith({ lang: 'es', engine: 'qwen3-tts', voice: 'voz-x' });
    expect(messages(notices)).toEqual([
      { message: 'Cargando la voz Qwen3-TTS…', duration: 0 },
      { message: 'La voz Qwen3-TTS está lista (7,0 s)', tone: 'success' },
    ]);
    expect(notices.dismissToast).toHaveBeenCalledWith('toast-1');
  });

  it('says nothing when the voice is already in memory', async () => {
    vi.mocked(ttsApi.getStatus).mockResolvedValue({ engine: 'piper', loaded: true, model_id: '' });
    const notices = sink();
    const { result } = renderHook(() => useLobbyVoice(notices));

    await act(() => result.current.prepare('es'));

    expect(ttsApi.load).not.toHaveBeenCalled();
    expect(notices.pushToast).not.toHaveBeenCalled();
  });

  it('uses the default engine when no voice is saved for this language', async () => {
    localStorage.setItem('tb_voice', JSON.stringify({ lang: 'quc', engine: 'mms' }));
    vi.mocked(ttsApi.getStatus).mockRejectedValue(new Error('offline'));
    vi.mocked(ttsApi.load).mockResolvedValue({ engine: 'piper', loaded: true, model_id: '', load_ms: 900 });
    const notices = sink();
    const { result } = renderHook(() => useLobbyVoice(notices));

    await act(() => result.current.prepare('es'));

    expect(ttsApi.load).toHaveBeenCalledWith({ lang: 'es', engine: undefined, voice: undefined });
    expect(messages(notices)[0]).toEqual({ message: 'Cargando la voz…', duration: 0 });
    expect(messages(notices)[1]).toEqual({ message: 'La voz Piper está lista (0,9 s)', tone: 'success' });
  });

  it.each([
    ['refused', () => vi.mocked(ttsApi.load).mockRejectedValue(new Error('503'))],
    ['not loaded', () => vi.mocked(ttsApi.load).mockResolvedValue({ engine: 'kokoro', loaded: false, model_id: '', load_ms: 0 })],
  ])('warns when the voice is %s, and the game goes on', async (_case, arrange) => {
    vi.mocked(ttsApi.getStatus).mockResolvedValue({ engine: 'kokoro', loaded: false, model_id: '' });
    arrange();
    const notices = sink();
    const { result } = renderHook(() => useLobbyVoice(notices));

    await act(() => result.current.prepare('es'));

    expect(messages(notices).at(-1)).toEqual({ message: VOICE_LOAD_FAILED, tone: 'warn' });
    expect(notices.dismissToast).toHaveBeenCalled();
  });

  it('unloads the voice the game loaded, and says so', async () => {
    vi.mocked(ttsApi.getStatus)
      .mockResolvedValueOnce({ engine: 'qwen3-tts', loaded: false, model_id: '' })
      .mockResolvedValueOnce({ engine: 'qwen3-tts', loaded: true, model_id: '' });
    vi.mocked(ttsApi.load).mockResolvedValue({ engine: 'qwen3-tts', loaded: true, model_id: '', load_ms: 1 });
    vi.mocked(ttsApi.unload).mockResolvedValue({ engine: 'all', loaded: false });
    const notices = sink();
    const { result } = renderHook(() => useLobbyVoice(notices));
    await act(() => result.current.prepare('quc'));

    await act(() => result.current.release());

    expect(ttsApi.getStatus).toHaveBeenLastCalledWith('qwen3-tts', 'quc');
    expect(ttsApi.unload).toHaveBeenCalledWith({});
    expect(messages(notices).at(-1)).toEqual({ message: VOICE_UNLOADED, tone: 'success' });
  });

  it('does nothing at the end when no voice is in memory', async () => {
    vi.mocked(ttsApi.getStatus).mockResolvedValue({ engine: 'piper', loaded: false, model_id: '' });
    const notices = sink();
    const { result } = renderHook(() => useLobbyVoice(notices));

    await act(() => result.current.release());

    expect(ttsApi.getStatus).toHaveBeenCalledWith(undefined, 'es');
    expect(ttsApi.unload).not.toHaveBeenCalled();
    expect(notices.pushToast).not.toHaveBeenCalled();
  });

  it('warns when the unload fails, and runs one release at a time', async () => {
    vi.mocked(ttsApi.getStatus).mockResolvedValue({ engine: 'piper', loaded: true, model_id: '' });
    vi.mocked(ttsApi.unload).mockRejectedValue(new Error('down'));
    const notices = sink();
    const { result } = renderHook(() => useLobbyVoice(notices));

    await act(async () => {
      await Promise.all([result.current.release(), result.current.release()]);
    });

    expect(ttsApi.unload).toHaveBeenCalledTimes(1);
    expect(messages(notices)).toEqual([{ message: VOICE_UNLOAD_FAILED, tone: 'warn' }]);
  });
});

describe('voiceName', () => {
  it('names known engines and passes unknown ids through', () => {
    expect(voiceName('qwen3-tts')).toBe('la voz Qwen3-TTS');
    expect(voiceName('espeak')).toBe('la voz eSpeak');
    expect(voiceName('nueva')).toBe('la voz nueva');
    expect(voiceName(null)).toBe('la voz');
  });
});
