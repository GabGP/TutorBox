import React from 'react';
import { Sheet } from '../../shared/ui/Sheet/Sheet';
import { BankQuestion } from './bankApi';
import { QuestionForm } from './QuestionForm';

export interface QuestionEditSheetProps {
  /** Null = closed. */
  question: BankQuestion | null;
  onClose: () => void;
  onSaved: (id: string) => void;
}

/**
 * Edit card for a bank question: same form as Crear, floating sheet
 * behaviour matching the user edit card.
 */
export const QuestionEditSheet: React.FC<QuestionEditSheetProps> = ({
  question,
  onClose,
  onSaved,
}) => {
  if (!question) return null;
  return (
    <Sheet label={`Editar pregunta ${question.id}`} onClose={onClose}>
      <QuestionForm
        key={question.id}
        initial={question}
        onCancel={onClose}
        onSaved={(id) => onSaved(id)}
      />
    </Sheet>
  );
};
