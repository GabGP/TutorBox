import { describe, expect, it, vi } from 'vitest';
import * as httpClient from '../../../shared/api/httpClient';
import { speechApi, ttsApi } from '../speechApi';

describe('ttsApi and speechApi client contracts', () => {
  it('getStatus sends GET /tts/status with query params', async () => {
    const spy = vi.spyOn(httpClient, 'requestApi').mockResolvedValue({
      engine: 'piper',
      loaded: true,
      model_id: 'es_ES-sharvard-medium.onnx',
    });

    const res = await ttsApi.getStatus('piper', 'es');
    expect(spy).toHaveBeenCalledWith('GET', '/tts/status?lang=es&engine=piper');
    expect(res.loaded).toBe(true);
    expect(res.engine).toBe('piper');
  });

  it('load sends POST /tts/load with payload', async () => {
    const spy = vi.spyOn(httpClient, 'requestApi').mockResolvedValue({
      engine: 'kokoro',
      loaded: true,
      model_id: 'kokoro-v1',
      load_ms: 120.5,
    });

    const res = await ttsApi.load({ engine: 'kokoro', lang: 'es', voice: 'es' });
    expect(spy).toHaveBeenCalledWith('POST', '/tts/load', {
      engine: 'kokoro',
      lang: 'es',
      voice: 'es',
    });
    expect(res.loaded).toBe(true);
    expect(res.load_ms).toBe(120.5);
  });

  it('unload sends POST /tts/unload with payload', async () => {
    const spy = vi.spyOn(httpClient, 'requestApi').mockResolvedValue({
      engine: 'piper',
      loaded: false,
    });

    const res = await ttsApi.unload({ engine: 'piper' });
    expect(spy).toHaveBeenCalledWith('POST', '/tts/unload', { engine: 'piper' });
    expect(res.loaded).toBe(false);
  });

  it('getVoices sends GET /tts/voices with language and engine', async () => {
    const spy = vi.spyOn(httpClient, 'requestApi').mockResolvedValue([
      { id: 'es_ES-sharvard-medium.onnx', lang: 'es', engine: 'piper' },
    ]);

    const res = await ttsApi.getVoices('es', 'piper');
    expect(spy).toHaveBeenCalledWith('GET', '/tts/voices?lang=es&engine=piper');
    expect(res).toHaveLength(1);
    expect(res[0].engine).toBe('piper');
  });

  it('speechApi.getSpeechBlobUrl requests blob URL', async () => {
    const spy = vi.spyOn(httpClient, 'requestBlobUrl').mockResolvedValue('blob:test');

    const res = await speechApi.getSpeechBlobUrl('session-123', 'quc');
    expect(spy).toHaveBeenCalledWith('/session/session-123/speech?lang=quc');
    expect(res).toBe('blob:test');
  });
});
