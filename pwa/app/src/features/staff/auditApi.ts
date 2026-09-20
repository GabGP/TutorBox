import { requestApi } from '../../shared/api/httpClient';

export interface AuditLogItem {
  id: number;
  actor_user_id: number | null;
  action: string;
  target_user_id: number | null;
  created_at: string | null;
}

/**
 * Admin-only audit log reader (`GET /staff/audit-logs`).
 * Callers must gate on `user.role === 'admin'` and hide on 403.
 */
export const auditApi = {
  async getAuditLogs(): Promise<AuditLogItem[]> {
    const res = await requestApi<{ logs: AuditLogItem[] }>(
      'GET',
      '/staff/audit-logs'
    );
    return res.logs || [];
  },
};
