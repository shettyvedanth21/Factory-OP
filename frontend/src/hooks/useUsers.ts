// React Query hooks for users
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { users } from '../api/endpoints';
import { FactoryUser, InviteUserRequest } from '../types';
import { useUIStore } from '../stores/uiStore';

const USERS_KEY = 'users';

export const useUsersList = () => {
  return useQuery({
    queryKey: [USERS_KEY, 'list'],
    queryFn: () => users.list(),
  });
};

export const useInviteUser = () => {
  const addNotification = useUIStore((state) => state.addNotification);
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: InviteUserRequest) => users.invite(data),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: [USERS_KEY] });
      addNotification({
        type: 'success',
        title: 'User invited',
        message: `Invitation sent to ${data.email}`,
      });
    },
    onError: (error: any) => {
      addNotification({
        type: 'error',
        title: 'Failed to invite user',
        message: error.message,
      });
    },
  });
};

export const useUpdateUserPermissions = () => {
  const addNotification = useUIStore((state) => state.addNotification);
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ userId, permissions }: { userId: number; permissions: Record<string, boolean> }) =>
      users.updatePermissions(userId, permissions),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [USERS_KEY] });
      addNotification({
        type: 'success',
        title: 'Permissions updated',
        message: 'User permissions have been updated',
      });
    },
    onError: (error: any) => {
      addNotification({
        type: 'error',
        title: 'Failed to update permissions',
        message: error.message,
      });
    },
  });
};

export const useDeactivateUser = () => {
  const addNotification = useUIStore((state) => state.addNotification);
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (userId: number) => users.deactivate(userId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [USERS_KEY] });
      addNotification({
        type: 'success',
        title: 'User deactivated',
        message: 'User has been deactivated',
      });
    },
    onError: (error: any) => {
      addNotification({
        type: 'error',
        title: 'Failed to deactivate user',
        message: error.message,
      });
    },
  });
};
