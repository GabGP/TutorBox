import React, { useEffect, useRef, useState } from 'react';
import { RotateCcw, Send, Star } from 'lucide-react';
import { type ChatMessage, useTutorChat } from './useTutorChat';
import styles from './tutor.module.css';

const MAX_CHARS = 280;
const TEXT_ONLY = 'Solo puedo leer texto, no imágenes. Escribe tu pregunta con palabras y números.';

/**
 * One message. Tutor hints above level 0 carry a "Pista N de 3" tag, and the praise for a
 * solved problem is the one pink (accent) bubble of the chat.
 */
const Message: React.FC<{ message: ChatMessage }> = ({ message }) => {
  if (message.role === 'student') return <p className={styles.studentBubble}>{message.text}</p>;
  if (message.kind === 'praise') {
    return (
      <div className={styles.praiseBubble}>
        <Star size={18} aria-hidden />
        <p>{message.text}</p>
      </div>
    );
  }
  if (message.kind === 'hint' && message.hintLevel) {
    return (
      <div className={styles.hint}>
        <span className={styles.hintTag}>Pista {message.hintLevel} de 3</span>
        <p className={styles.tutorBubble}>{message.text}</p>
      </div>
    );
  }
  return <p className={styles.tutorBubble}>{message.text}</p>;
};

/**
 * The student's Socratic math tutor chat. Text only: there is no attachment button, and
 * pasted or dropped files (e.g. a photo of the homework) are refused before they reach
 * the input. The backend guards the same rule.
 *
 * @param {object} props - `username` of the logged-in student.
 */
export const TutorChat: React.FC<{ username: string }> = ({ username }) => {
  const { messages, sending, error, send, reset } = useTutorChat(username);
  const [draft, setDraft] = useState('');
  const [notice, setNotice] = useState<string | null>(null);
  const listRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const list = listRef.current;
    if (list) list.scrollTop = list.scrollHeight;
  }, [messages, sending]);

  const submit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (await send(draft)) setDraft('');
  };

  const refuseFiles = (files: FileList | undefined, event: React.SyntheticEvent) => {
    if (files && files.length > 0) {
      event.preventDefault();
      setNotice(TEXT_ONLY);
    }
  };

  return (
    <section className={styles.chat} aria-label="Tutor de matemáticas">
      <div className={styles.chatHead}>
        <h2>Tutor de matemáticas</h2>
        <button type="button" className={styles.ghost} onClick={() => void reset()} disabled={sending}>
          <RotateCcw size={16} aria-hidden /> Empezar de nuevo
        </button>
      </div>

      <div className={styles.list} ref={listRef} role="log" aria-live="polite">
        <p className={styles.tutorBubble}>
          ¡Hola, {username}! Escríbeme un problema, por ejemplo 23 + 45, o pregúntame algo como «¿qué es
          una fracción?». No te doy la respuesta: te ayudo a encontrarla.
        </p>
        {messages.map((message) => (
          <Message key={message.id} message={message} />
        ))}
        {sending && (
          <p className={`${styles.tutorBubble} ${styles.thinking}`}>
            <span className={styles.dots} aria-hidden>
              <i />
              <i />
              <i />
            </span>
            El tutor está pensando…
          </p>
        )}
      </div>

      {(error || notice) && (
        <p className={styles.alert} role="alert">
          {error || notice}
        </p>
      )}

      <form className={styles.composer} onSubmit={submit}>
        <input
          type="text"
          value={draft}
          maxLength={MAX_CHARS}
          onChange={(event) => {
            setDraft(event.target.value);
            setNotice(null);
          }}
          onPaste={(event) => refuseFiles(event.clipboardData?.files, event)}
          onDrop={(event) => refuseFiles(event.dataTransfer?.files, event)}
          placeholder="Escribe tu pregunta de matemáticas…"
          aria-label="Tu mensaje para el tutor"
          autoComplete="off"
          enterKeyHint="send"
        />
        <button type="submit" className={styles.send} disabled={sending || !draft.trim()} aria-label="Enviar">
          <Send size={20} aria-hidden />
        </button>
      </form>
    </section>
  );
};
