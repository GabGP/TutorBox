import { useCallback, useEffect, useRef, useState } from 'react';
import { ApiError } from '../../shared/api/httpClient';
import { tutorApi } from './tutorApi';

export interface ChatMessage {
  id: number;
  role: 'student' | 'tutor';
  text: string;
}

const PING_INTERVAL_MS = 20_000;

/** Reads the conversation kept for this tab (it survives a reload of the sign-in window). */
function loadMessages(key: string): ChatMessage[] {
  try {
    const raw = sessionStorage.getItem(key);
    return raw ? (JSON.parse(raw) as ChatMessage[]) : [];
  } catch {
    return [];
  }
}

function saveMessages(key: string, messages: ChatMessage[]): void {
  try {
    sessionStorage.setItem(key, JSON.stringify(messages));
  } catch {
    // Private mode or full storage: the chat still works, it just is not kept.
  }
}

/**
 * State of the student's tutor chat: messages, the pending reply and errors.
 * While mounted it pings the backend so the teacher sees the student as connected.
 *
 * @param {string} username - Owner of the conversation (keys the stored history).
 * @param {object} [options] - `pingIntervalMs` for tests.
 */
export function useTutorChat(username: string, options: { pingIntervalMs?: number } = {}) {
  const { pingIntervalMs = PING_INTERVAL_MS } = options;
  const storageKey = `tb_tutor_chat:${username}`;
  const [messages, setMessages] = useState<ChatMessage[]>(() => loadMessages(storageKey));
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const sendingRef = useRef(false);

  useEffect(() => saveMessages(storageKey, messages), [storageKey, messages]);

  useEffect(() => {
    const ping = () => void tutorApi.ping().catch(() => undefined);
    ping();
    const timer = setInterval(ping, pingIntervalMs);
    return () => clearInterval(timer);
  }, [pingIntervalMs]);

  const append = (role: ChatMessage['role'], text: string) =>
    setMessages((current) => [
      ...current,
      { id: (current[current.length - 1]?.id ?? 0) + 1, role, text },
    ]);

  const send = useCallback(async (draft: string): Promise<boolean> => {
    const message = draft.trim();
    if (!message || sendingRef.current) return false;
    sendingRef.current = true;
    setSending(true);
    setError(null);
    append('student', message);
    try {
      const reply = await tutorApi.send(message);
      append('tutor', reply.reply);
      return true;
    } catch (err) {
      setError(err instanceof ApiError ? err.detail || err.message : 'No se pudo enviar el mensaje.');
      return false;
    } finally {
      sendingRef.current = false;
      setSending(false);
    }
  }, []);

  const reset = useCallback(async () => {
    await tutorApi.reset().catch(() => undefined);
    setMessages([]);
    setError(null);
  }, []);

  return { messages, sending, error, send, reset };
}
