// React Query hooks for devices
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { devices } from '../api/endpoints';
import { DeviceCreate, DeviceUpdate } from '../types';
import { useUIStore } from '../stores/uiStore';

const DEVICES_KEY = 'devices';

export const useDevices = (filters?: { page?: number; per_page?: number; search?: string; is_active?: boolean }) => {
  return useQuery({
    queryKey: [DEVICES_KEY, filters],
    queryFn: () => devices.list(filters),
  });
};

export const useDevice = (deviceId: number) => {
  return useQuery({
    queryKey: [DEVICES_KEY, deviceId],
    queryFn: () => devices.getById(deviceId),
    enabled: !!deviceId,
  });
};

export const useCreateDevice = () => {
  const queryClient = useQueryClient();
  const addNotification = useUIStore((state) => state.addNotification);

  return useMutation({
    mutationFn: (data: DeviceCreate) => devices.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [DEVICES_KEY] });
      addNotification({
        type: 'success',
        title: 'Device created',
        message: 'New device registered successfully',
      });
    },
    onError: (error: any) => {
      addNotification({
        type: 'error',
        title: 'Failed to create device',
        message: error.message,
      });
    },
  });
};

export const useUpdateDevice = () => {
  const queryClient = useQueryClient();
  const addNotification = useUIStore((state) => state.addNotification);

  return useMutation({
    mutationFn: ({ deviceId, data }: { deviceId: number; data: DeviceUpdate }) =>
      devices.update(deviceId, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: [DEVICES_KEY, variables.deviceId] });
      queryClient.invalidateQueries({ queryKey: [DEVICES_KEY] });
      addNotification({
        type: 'success',
        title: 'Device updated',
        message: 'Device information updated successfully',
      });
    },
    onError: (error: any) => {
      addNotification({
        type: 'error',
        title: 'Failed to update device',
        message: error.message,
      });
    },
  });
};

export const useDeleteDevice = () => {
  const queryClient = useQueryClient();
  const addNotification = useUIStore((state) => state.addNotification);

  return useMutation({
    mutationFn: (deviceId: number) => devices.delete(deviceId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [DEVICES_KEY] });
      addNotification({
        type: 'success',
        title: 'Device deactivated',
        message: 'Device has been deactivated',
      });
    },
    onError: (error: any) => {
      addNotification({
        type: 'error',
        title: 'Failed to deactivate device',
        message: error.message,
      });
    },
  });
};
