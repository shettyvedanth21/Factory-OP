// React Query hooks for dashboard
import { useQuery } from '@tanstack/react-query';
import { dashboard } from '../api/endpoints';

const DASHBOARD_KEY = 'dashboard';

export const useDashboardSummary = () => {
  return useQuery({
    queryKey: [DASHBOARD_KEY, 'summary'],
    queryFn: () => dashboard.getSummary(),
    refetchInterval: 30000, // Refetch every 30 seconds
  });
};
