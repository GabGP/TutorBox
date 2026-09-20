import React, { useState } from 'react';
import { QuestionBankView } from '../../features/question-bank/QuestionBankView';
import { QuestionForm } from '../../features/question-bank/QuestionForm';
import { QuestionGenerationProgress } from '../../features/question-generator/QuestionGenerationProgress';
import { getTopicLabel } from '../../features/question-generator/TopicSelector';
import { TelemetryView } from '../../features/question-generator/TelemetryView';
import {
  GenerationProgress,
} from '../../features/question-generator/generator.types';
import generatorStyles from '../../features/question-generator/generator.module.css';
import rosterStyles from '../../features/roster/roster.module.css';
import { SourceSwitch } from './SourceSwitch';
import { Collapsible } from '../../shared/ui/Collapsible/Collapsible';

export type BankTab = 'elegir' | 'crear' | 'pregrow';

const BANK_TABS = [
  { value: 'elegir', glyph: '☑', label: 'Elegir' },
  { value: 'crear', glyph: '＋', label: 'Crear' },
  { value: 'pregrow', glyph: '⚡', label: 'Pre-generar' },
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
    <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }} id="s-bank">
      <SourceSwitch<BankTab>
        value={tab}
        onChange={setTab}
        options={[...BANK_TABS]}
        ariaLabel="Sección del banco"
      />

      {tab === 'elegir' && (
        <>
          <p style={{ fontSize: '15px', color: 'var(--mute2)', margin: 0 }}>
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
            <div className={rosterStyles.alert}>{createNotice}</div>
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
                onClick={() => onChangeCount(Math.max(1, count - 1))}
              >
                −
              </button>
              <button
                type="button"
                className={generatorStyles.p}
                aria-label="Pre-generar una más"
                onClick={() => onChangeCount(Math.min(20, count + 1))}
              >
                +
              </button>
            </div>
          </div>
          <div className={rosterStyles.addForm}>
            <button
              type="button"
              className={rosterStyles.submitAdd}
              onClick={handlePregenerate}
              disabled={pregenerating}
            >
              {pregenerating ? 'Generando…' : '＋ Pre-generar en banco'}
            </button>
          </div>
          {progress && (
            <QuestionGenerationProgress progress={progress} isComplete={false} />
          )}
          {genError && (
            <div className={rosterStyles.errorBanner}>{genError}</div>
          )}
          <p style={{ fontSize: '15px', color: 'var(--mute2)', margin: 0 }}>
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
