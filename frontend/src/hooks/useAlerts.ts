// React Query hooks for alerts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { alerts } from '../api/endpoints';
import { AlertFilters } from '../types';
import { useUIStore } from '../stores/uiStore';

const ALERTS_KEY = 'alerts';

export const useAlerts = (filters?: AlertFilters & { page?: number; per_page?: number }) => {
  return useQuery({
    queryKey: [ALERTS_KEY, filters],
    queryFn: () => alerts.list(filters),
  });
};

export const useAlert = (alertId: number) => {
  return useQuery({
    queryKey: [ALERTS_KEY, alertId],
    queryFn: () => alerts.getById(alertId),
    enabled: !!alertId,
  });
};

export const useResolveAlert = () => {
  const queryClient = useQueryClient();
  const addNotification = useUIStore((state) => state.addNotification);

  return useMutation({
    mutationFn: (alertId: number) => alerts.resolve(alertId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [ALERTS_KEY] });
      addNotification({
        type: 'success',
        title: 'Alert resolved',
        message: 'Alert has been marked as resolved',
      });
    },
    onError: (error: any) => {
      addNotification({
        type: 'error',
        title: 'Failed to resolve alert',
        message: error.message,
      });
    },
  });
};
