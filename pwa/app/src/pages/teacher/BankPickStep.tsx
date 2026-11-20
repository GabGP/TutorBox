import React, { useEffect, useState } from 'react';
import { BookOpen, Minus, Play, Plus, Square, X, Zap } from 'lucide-react';
import { QuestionBankView } from '../../features/question-bank/QuestionBankView';
import { QuestionForm } from '../../features/question-bank/QuestionForm';
import { QuestionGenerationProgress } from '../../features/question-generator/QuestionGenerationProgress';
import { getTopicLabel } from '../../shared/taxonomy/labels';
import { TelemetryView } from '../../features/question-generator/TelemetryView';
import {
  GenerationProgress,
} from '../../features/question-generator/generator.types';
import {
  QUESTION_COUNT_MAX,
  QUESTION_COUNT_MIN,
} from '../../features/question-generator/generator.constants';
import generatorStyles from '../../features/question-generator/generator.module.css';
import formStyles from '../../shared/styles/forms.module.css';
import { ToastViewport } from '../../shared/ui/Toast/ToastViewport';
import { useToastQueue } from '../../shared/ui/Toast/useToastQueue';
import utils from '../../shared/styles/utils.module.css';
import styles from './BankPickStep.module.css';
import { SourceSwitch } from './SourceSwitch';
import { Collapsible } from '../../shared/ui/Collapsible/Collapsible';

export type BankTab = 'elegir' | 'crear' | 'generar';

const BANK_TABS = [
  { value: 'elegir', icon: BookOpen, label: 'Elegir' },
  { value: 'crear', icon: Plus, label: 'Crear' },
  { value: 'generar', icon: Zap, label: 'Generar' },
] as const;

export interface BankPickStepProps {
  selectedTopic: string;
  count: number;
  onChangeCount: (n: number) => void;
  genError?: string | null;
  progress: GenerationProgress | null;
  generating: boolean;
  /** Detener was pressed: creation waits for Reanudar or Cancelar. */
  generationPaused?: boolean;
  onStopGeneration?: () => void;
  onResumeGeneration?: () => void;
  onCancelGeneration?: () => void;
  bankIds: string[];
  onToggleBankId: (id: string) => void;
  onEnsureBankIds: (ids: string[]) => void;
  onGenerate: () => Promise<unknown>;
  isAdmin?: boolean;
}

/**
 * Quiz-prep bank picker: hand-pick stored questions (Elegir), write one
 * manually (Crear), or fill the bank on demand (Generar), with the
 * generation activity log underneath. The match is built only from the
 * chosen questions — no generation involved. Generation failures
 * float as error toasts so the layout never shifts.
 */
export const BankPickStep: React.FC<BankPickStepProps> = ({
  selectedTopic,
  count,
  onChangeCount,
  genError,
  progress,
  generating,
  generationPaused = false,
  onStopGeneration,
  onResumeGeneration,
  onCancelGeneration,
  bankIds,
  onToggleBankId,
  onEnsureBankIds,
  onGenerate,
  isAdmin = false,
}) => {
  const [tab, setTab] = useState<BankTab>('elegir');
  const [reloadKey, setReloadKey] = useState(0);
  const { toasts, pushToast, dismissToast } = useToastQueue();

  useEffect(() => {
    if (genError) pushToast({ message: genError, tone: 'error' });
  }, [genError, pushToast]);

  const handleGenerate = async () => {
    const ids = (await onGenerate()) as unknown;
    if (Array.isArray(ids) && ids.length > 0) {
      onEnsureBankIds(ids as string[]);
      setReloadKey((k) => k + 1);
    } else {
      setReloadKey((k) => k + 1);
    }
  };

  const handleCreated = (id: string) => {
    onEnsureBankIds([id]);
    setReloadKey((k) => k + 1);
    pushToast({ message: `Pregunta guardada (${id}) y elegida para el juego.` });
    setTab('elegir');
  };

  return (
    <div className={styles.stack} id="s-bank">
      <SourceSwitch<BankTab>
        value={tab}
        onChange={setTab}
        options={[...BANK_TABS]}
        ariaLabel="Sección del banco"
      />

      {tab === 'elegir' && (
        <>
          <p className={styles.description}>
            Toca una pregunta para ver y editar sus opciones ({getTopicLabel(selectedTopic)}).
            El juego se crea solo con las que elijas, sin generar.
          </p>
          <QuestionBankView
            selectable
            selectedIds={bankIds}
            onToggleSelect={onToggleBankId}
            reloadKey={reloadKey}
            initialTopic={selectedTopic}
            isAdmin={isAdmin}
          />
        </>
      )}

      {tab === 'crear' && (
        <QuestionForm initial={null} onSaved={handleCreated} />
      )}

      {tab === 'generar' && (
        <>
          {/* While it runs, the status card takes the counter's place, as in the lobby. */}
          {generating && progress ? (
            <QuestionGenerationProgress
              progress={progress}
              isComplete={false}
              isPaused={generationPaused}
            />
          ) : (
            <div className={generatorStyles.counter}>
              <div className={generatorStyles.num}>{count}</div>
              <div className={generatorStyles.sub}>
                para generar · {getTopicLabel(selectedTopic)}
              </div>
              <div className={generatorStyles.pm}>
                <button
                  type="button"
                  aria-label="Generar una menos"
                  onClick={() => onChangeCount(Math.max(QUESTION_COUNT_MIN, count - 1))}
                >
                  <Minus size={28} aria-hidden />
                </button>
                <button
                  type="button"
                  className={generatorStyles.p}
                  aria-label="Generar una más"
                  onClick={() => onChangeCount(Math.min(QUESTION_COUNT_MAX, count + 1))}
                >
                  <Plus size={28} aria-hidden />
                </button>
              </div>
            </div>
          )}
          <div className={formStyles.addForm}>
            {!generating && (
              <button type="button" className={formStyles.submitAdd} onClick={handleGenerate}>
                <span className={utils.rowInline6}><Plus size={18} aria-hidden /> Generar en banco</span>
              </button>
            )}
            {generating && !generationPaused && (
              <button type="button" className={formStyles.submitAdd} onClick={onStopGeneration}>
                <span className={utils.rowInline6}><Square size={16} aria-hidden /> Detener</span>
              </button>
            )}
            {generating && generationPaused && (
              <>
                <button type="button" className={formStyles.submitAdd} onClick={onCancelGeneration}>
                  <span className={utils.rowInline6}><X size={18} aria-hidden /> Cancelar</span>
                </button>
                <button type="button" className={formStyles.submitAdd} onClick={onResumeGeneration}>
                  <span className={utils.rowInline6}><Play size={16} aria-hidden /> Reanudar</span>
                </button>
              </>
            )}
          </div>
          <p className={styles.description}>
            Las nuevas preguntas se eligen solas para el juego.
          </p>
        </>
      )}

      <Collapsible title="Actividad de generación">
        <TelemetryView />
      </Collapsible>
      <ToastViewport toasts={toasts} onDismiss={(id) => dismissToast(id)} />
    </div>
  );
};
