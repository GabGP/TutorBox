import React, { useId, useState } from 'react';
import { Plus } from 'lucide-react';
import formStyles from '../../shared/styles/forms.module.css';
import { clickerIdError } from './clickerId';
import styles from './clickers.module.css';

export interface ClickerAddFormProps {
  /** Registers the trimmed id. Rejects when the server refuses it (the parent toasts). */
  onRegister: (deviceId: string) => Promise<unknown>;
}

/**
 * Adds one clicker by its hardware label. The id is checked here first, so
 * a malformed id shows inline and never reaches the server. Server refusals
 * (409, 422, others) arrive as error toasts from the parent. The typed text
 * stays after a refusal so the teacher can correct it; it clears on success.
 * The field stays hidden behind Agregar por código until the teacher asks for
 * it: an input on screen when the sheet opens let a phone raise its keyboard
 * on its own, and new clickers appear by themselves anyway.
 */
export const ClickerAddForm: React.FC<ClickerAddFormProps> = ({ onRegister }) => {
  const [open, setOpen] = useState(false);
  const [typedId, setTypedId] = useState('');
  const [inlineError, setInlineError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const errorId = useId();

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!typedId.trim()) return;
    const validationError = clickerIdError(typedId);
    setInlineError(validationError);
    if (validationError) return;

    setBusy(true);
    try {
      await onRegister(typedId.trim());
      setTypedId('');
    } catch {
      // The parent hook already showed the error toast.
    } finally {
      setBusy(false);
    }
  };

  const toggle = (
    <button
      type="button"
      className={formStyles.toggleLink}
      aria-expanded={open}
      onClick={() => {
        setOpen((wasOpen) => !wasOpen);
        setInlineError(null);
      }}
    >
      {open ? (
        'Ocultar'
      ) : (
        <>
          <Plus size={16} aria-hidden /> Agregar por código
        </>
      )}
    </button>
  );

  if (!open) return <div className={styles.addStack}>{toggle}</div>;

  return (
    <div className={styles.addStack}>
      {toggle}
      <form className={formStyles.addForm} onSubmit={handleSubmit} noValidate>
        <input
          id="newClicker"
          type="text"
          className={`${formStyles.addInput} ${formStyles.fill}`}
          aria-label="Código del clicker"
          placeholder="Código de la etiqueta (ej. ESP32-A4CF12)"
          maxLength={32}
          autoCapitalize="off"
          autoCorrect="off"
          spellCheck={false}
          autoComplete="off"
          // Opened on purpose to type a code, so the keyboard may come up now.
          autoFocus
          value={typedId}
          onChange={(event) => {
            setTypedId(event.target.value);
            setInlineError(null);
          }}
          disabled={busy}
          aria-invalid={inlineError ? true : undefined}
          aria-describedby={inlineError ? errorId : undefined}
        />
        <button
          type="submit"
          className={`${formStyles.submitAdd} ${styles.addButton}`}
          disabled={busy || !typedId.trim()}
        >
          Agregar
        </button>
      </form>
      {inlineError && (
        <div id={errorId} className={formStyles.errorBanner} role="alert">
          {inlineError}
        </div>
      )}
    </div>
  );
};
