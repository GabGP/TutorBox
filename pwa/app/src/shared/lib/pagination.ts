import { useState } from 'react';

/**
 * Offset pagination state shared by Bank and Telemetry list shells.
 */
export function usePagination(initialPageSize = 20) {
  const [offset, setOffset] = useState(0);
  const [pageSize, setPageSize] = useState(initialPageSize);
  const page = Math.floor(offset / pageSize);

  const clamp = (total: number, nextOffset: number) => {
    const safe = Math.max(0, nextOffset);
    if (total > 0 && safe >= total) {
      return Math.max(0, (Math.ceil(total / pageSize) - 1) * pageSize);
    }
    return safe;
  };

  return { offset, setOffset, pageSize, setPageSize, page, clamp };
}

/**
 * Two-tap destructive confirm. Replaces the confirmDelete/confirmName
 * boolean dances in AccountCard, QuestionBankView and UserEditSheet.
 */
export function useConfirmAction(timeoutMs = 4000) {
  const [confirming, setConfirming] = useState(false);

  const request = () => setConfirming(true);
  const cancel = () => setConfirming(false);

  const wrap = (fn: () => void | Promise<void>) => async () => {
    if (!confirming) {
      request();
      if (timeoutMs > 0) {
        setTimeout(() => setConfirming(false), timeoutMs);
      }
      return;
    }
    await fn();
    setConfirming(false);
  };

  return { confirming, request, cancel, wrap };
}
