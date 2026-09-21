import React, { useState } from 'react';
import { Minus, Plus, SquareCheck, Zap } from 'lucide-react';
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
import utils from '../../shared/styles/utils.module.css';
import styles from './BankPickStep.module.css';
import { SourceSwitch } from './SourceSwitch';
import { Collapsible } from '../../shared/ui/Collapsible/Collapsible';

export type BankTab = 'elegir' | 'crear' | 'pregrow';

const BANK_TABS = [
  { value: 'elegir', icon: SquareCheck, label: 'Elegir' },
  { value: 'crear', icon: Plus, label: 'Crear' },
  { value: 'pregrow', icon: Zap, label: 'Pre-generar' },
] as const;

export interface BankPickStepProps {
  selectedTopic: string;
  count: number;
  onChangeCount: (n: number) => void;
  genError?: string | null;
  progress: GenerationProgress | null;
  pregenerating: boolean;
  bankIds: string[];
  onToggleBankId: (id: string) => void;
  onEnsureBankIds: (ids: string[]) => void;
  onPregenerate: () => Promise<unknown>;
  isAdmin?: boolean;
}

/**
 * Quiz-prep bank picker: hand-pick stored questions (Elegir), write one
 * manually (Crear), or fill the bank on demand (Pre-generar), with the
 * generation activity log underneath. The match is built only from the
 * chosen questions — no generation involved.
 */
export const BankPickStep: React.FC<BankPickStepProps> = ({
  selectedTopic,
  count,
  onChangeCount,
  genError,
  progress,
  pregenerating,
  bankIds,
  onToggleBankId,
  onEnsureBankIds,
  onPregenerate,
  isAdmin = false,
}) => {
  const [tab, setTab] = useState<BankTab>('elegir');
  const [reloadKey, setReloadKey] = useState(0);
  const [createNotice, setCreateNotice] = useState<string | null>(null);

  const handlePregenerate = async () => {
    const ids = (await onPregenerate()) as unknown;
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
    setCreateNotice(`Pregunta guardada (${id}) y elegida para el juego.`);
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
            Marca las preguntas que quieres usar ({getTopicLabel(selectedTopic)}). El juego
            se crea solo con las elegidas, sin generar.
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
        <>
          {createNotice && (
            <div className={formStyles.alert}>{createNotice}</div>
          )}
          <QuestionForm initial={null} onSaved={handleCreated} />
        </>
      )}

      {tab === 'pregrow' && (
        <>
          <div className={generatorStyles.counter}>
            <div className={generatorStyles.num}>{count}</div>
            <div className={generatorStyles.sub}>
              para pre-generar · {getTopicLabel(selectedTopic)}
            </div>
            <div className={generatorStyles.pm}>
              <button
                type="button"
                aria-label="Pre-generar una menos"
                onClick={() => onChangeCount(Math.max(QUESTION_COUNT_MIN, count - 1))}
              >
                <Minus size={28} aria-hidden />
              </button>
              <button
                type="button"
                className={generatorStyles.p}
                aria-label="Pre-generar una más"
                onClick={() => onChangeCount(Math.min(QUESTION_COUNT_MAX, count + 1))}
              >
                <Plus size={28} aria-hidden />
              </button>
            </div>
          </div>
          <div className={formStyles.addForm}>
            <button
              type="button"
              className={formStyles.submitAdd}
              onClick={handlePregenerate}
              disabled={pregenerating}
            >
              {pregenerating ? 'Generando…' : <span className={utils.rowInline6}><Plus size={18} aria-hidden /> Pre-generar en banco</span>}
            </button>
          </div>
          {progress && (
            <QuestionGenerationProgress progress={progress} isComplete={false} />
          )}
          {genError && (
            <div className={formStyles.errorBanner}>{genError}</div>
          )}
          <p className={styles.description}>
            Las nuevas preguntas se eligen solas para el juego.
          </p>
        </>
      )}

      <Collapsible title="Actividad de generación">
        <TelemetryView />
      </Collapsible>
    </div>
  );
};
