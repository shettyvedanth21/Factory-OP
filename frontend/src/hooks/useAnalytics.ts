// React Query hooks for analytics
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { analytics } from '../api/endpoints';
import { StartAnalyticsJobRequest } from '../types';
import { useUIStore } from '../stores/uiStore';

const ANALYTICS_KEY = 'analytics';

export const useStartJob = () => {
  const queryClient = useQueryClient();
  const addNotification = useUIStore((state) => state.addNotification);

  return useMutation({
    mutationFn: (data: StartAnalyticsJobRequest) => analytics.startJob(data),
    onSuccess: (data) => {
      addNotification({
        type: 'success',
        title: 'Analytics job started',
        message: `Job ID: ${data.job_id}`,
      });
    },
    onError: (error: any) => {
      addNotification({
        type: 'error',
        title: 'Failed to start job',
        message: error.message,
      });
    },
  });
};

export const useJob = (jobId: string) => {
  return useQuery({
    queryKey: [ANALYTICS_KEY, 'job', jobId],
    queryFn: () => analytics.getJob(jobId),
    enabled: !!jobId,
    refetchInterval: (data) => {
      // Stop polling when job is complete or failed
      if (data?.status === 'complete' || data?.status === 'failed') {
        return false;
      }
      // Poll every 3 seconds while running
      return 3000;
    },
  });
};
