// React Query hooks for reports
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { reports } from '../api/endpoints';
import { CreateReportRequest } from '../types';
import { useUIStore } from '../stores/uiStore';

const REPORTS_KEY = 'reports';

export const useReportsList = (params?: { status?: string; page?: number; per_page?: number }) => {
  return useQuery({
    queryKey: [REPORTS_KEY, 'list', params],
    queryFn: () => reports.list(params),
  });
};

export const useCreateReport = () => {
  const addNotification = useUIStore((state) => state.addNotification);
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CreateReportRequest) => reports.create(data),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: [REPORTS_KEY] });
      addNotification({
        type: 'success',
        title: 'Report generation started',
        message: `Report ID: ${data.report_id}`,
      });
    },
    onError: (error: any) => {
      addNotification({
        type: 'error',
        title: 'Failed to create report',
        message: error.message,
      });
    },
  });
};

export const useReport = (reportId: string) => {
  return useQuery({
    queryKey: [REPORTS_KEY, reportId],
    queryFn: () => reports.getById(reportId),
    enabled: !!reportId,
    refetchInterval: (data) => {
      // Stop polling when report is complete or failed
      if (data?.status === 'complete' || data?.status === 'failed') {
        return false;
      }
      // Poll every 5 seconds while running
      return 5000;
    },
  });
};

export const useDownloadReport = () => {
  const addNotification = useUIStore((state) => state.addNotification);

  return useMutation({
    mutationFn: async (reportId: string) => {
      const response = await reports.download(reportId);
      // Create blob URL and trigger download
      const blob = new Blob([response.data]);
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `report-${reportId}`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    },
    onSuccess: () => {
      addNotification({
        type: 'success',
        title: 'Report downloaded',
        message: 'Report has been downloaded successfully',
      });
    },
    onError: (error: any) => {
      addNotification({
        type: 'error',
        title: 'Failed to download report',
        message: error.message,
      });
    },
  });
};

export const useDeleteReport = () => {
  const addNotification = useUIStore((state) => state.addNotification);
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (reportId: string) => reports.delete(reportId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [REPORTS_KEY] });
      addNotification({
        type: 'success',
        title: 'Report deleted',
        message: 'Report has been deleted successfully',
      });
    },
    onError: (error: any) => {
      addNotification({
        type: 'error',
        title: 'Failed to delete report',
        message: error.message,
      });
    },
  });
};
