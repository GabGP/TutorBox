import React from 'react';
import { EntryForm, EntryFormProps } from './EntryForm';

export type LoginFormProps = EntryFormProps;

/**
 * Backwards-compatible alias: the unified `EntryForm` is the canonical
 * entry point for all roles. This wrapper keeps existing imports working.
 */
export const LoginForm: React.FC<LoginFormProps> = (props) => {
  return <EntryForm {...props} />;
};
