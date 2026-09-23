import React from 'react';
import { getRoleLabel } from '../../shared/constants/roles';
import formStyles from '../../shared/styles/forms.module.css';
import { getTopicLabel } from '../../shared/taxonomy/labels';
import type { TopicModel } from './generator.types';

export interface TelemetryFilterUser {
  id: string;
  username: string;
  role: string;
}

export interface TelemetryFiltersProps {
  topics: TopicModel[];
  topic: string;
  successFilter: string;
  userId: string;
  userOptions: TelemetryFilterUser[];
  extraUserIds: string[];
  onTopicChange: (value: string) => void;
  onSuccessFilterChange: (value: string) => void;
  onUserIdChange: (value: string) => void;
}

/** Topic/result/user filter row for the generation attempt log. */
export const TelemetryFilters: React.FC<TelemetryFiltersProps> = ({
  topics,
  topic,
  successFilter,
  userId,
  userOptions,
  extraUserIds,
  onTopicChange,
  onSuccessFilterChange,
  onUserIdChange,
}) => (
  <div className={formStyles.addForm}>
    <select
      className={`${formStyles.addInput} ${formStyles.fill}`}
      value={topic}
      onChange={(e) => onTopicChange(e.target.value)}
      aria-label="Tema"
    >
      <option value="">Todos los temas</option>
      {topics.map((t) => (
        <option key={t.name} value={t.name}>
          {t.label || getTopicLabel(t.name)}
        </option>
      ))}
    </select>
    <select
      className={`${formStyles.addInput} ${formStyles.pin130}`}
      value={successFilter}
      onChange={(e) => onSuccessFilterChange(e.target.value)}
      aria-label="Resultado"
    >
      <option value="">Todos</option>
      <option value="true">Éxitos</option>
      <option value="false">Fallos</option>
    </select>
    <select
      className={`${formStyles.addInput} ${formStyles.pin150}`}
      value={userId}
      onChange={(e) => onUserIdChange(e.target.value)}
      aria-label="ID de usuario"
    >
      <option value="">Todos los usuarios</option>
      {userOptions.map((u) => (
        <option key={u.id} value={u.id}>
          {u.username} · {getRoleLabel(u.role)}
        </option>
      ))}
      {extraUserIds.map((id) => (
        <option key={id} value={id}>
          #{id}
        </option>
      ))}
    </select>
  </div>
);
