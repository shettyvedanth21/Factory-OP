// React Query hooks for KPIs
import { useQuery } from '@tanstack/react-query';
import { kpis } from '../api/endpoints';
import { KPIHistoryParams } from '../types';

const KPIS_KEY = 'kpis';

export const useKPIsLive = (deviceId: number) => {
  return useQuery({
    queryKey: [KPIS_KEY, 'live', deviceId],
    queryFn: () => kpis.getLive(deviceId),
    refetchInterval: 5000, // Refetch every 5 seconds
    staleTime: 3000, // Consider data stale after 3 seconds
    enabled: !!deviceId,
  });
};

export const useKPIHistory = (deviceId: number, params: KPIHistoryParams) => {
  return useQuery({
    queryKey: [KPIS_KEY, 'history', deviceId, params],
    queryFn: () => kpis.getHistory(deviceId, params),
    enabled: !!deviceId && !!params.parameter,
  });
};
