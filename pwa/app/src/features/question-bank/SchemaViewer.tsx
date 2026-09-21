import React, { useState } from 'react';
import { toErrorMessage } from '../../shared/lib/errors';
import { bankApi } from './bankApi';
import styles from './SchemaViewer.module.css';

export interface SchemaViewerProps {
  onError: (message: string) => void;
}

/**
 * Admin-only JSON contract viewer: lazy-fetches the canonical question
 * schema on first open, toggles closed without refetching.
 */
export const SchemaViewer: React.FC<SchemaViewerProps> = ({ onError }) => {
  const [schema, setSchema] = useState<string | null>(null);

  const toggleSchema = async () => {
    if (schema !== null) {
      setSchema(null);
      return;
    }
    try {
      const s = await bankApi.getSchema();
      setSchema(JSON.stringify(s, null, 2));
    } catch (err: unknown) {
      onError(toErrorMessage(err, 'Error al cargar esquema'));
    }
  };

  return (
    <details>
      <summary className={styles.toggle} onClick={toggleSchema}>
        Contrato JSON de preguntas
      </summary>
      {schema && (
        <>
          <p className={styles.blurb}>
            Esquema oficial que debe cumplir cada pregunta del banco (el generador
            y la validación lo usan para aceptar o rechazar preguntas).
          </p>
          <pre className={styles.code}>{schema}</pre>
        </>
      )}
    </details>
  );
};
