// React Query hooks for rules
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { rules } from '../api/endpoints';
import { RuleCreate, RuleUpdate } from '../types';
import { useUIStore } from '../stores/uiStore';

const RULES_KEY = 'rules';

export const useRules = (filters?: { device_id?: number; is_active?: boolean; scope?: string; page?: number; per_page?: number }) => {
  return useQuery({
    queryKey: [RULES_KEY, filters],
    queryFn: () => rules.list(filters),
  });
};

export const useRule = (ruleId: number) => {
  return useQuery({
    queryKey: [RULES_KEY, ruleId],
    queryFn: () => rules.getById(ruleId),
    enabled: !!ruleId,
  });
};

export const useCreateRule = () => {
  const queryClient = useQueryClient();
  const addNotification = useUIStore((state) => state.addNotification);

  return useMutation({
    mutationFn: (data: RuleCreate) => rules.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [RULES_KEY] });
      addNotification({
        type: 'success',
        title: 'Rule created',
        message: 'New rule has been created',
      });
    },
    onError: (error: any) => {
      addNotification({
        type: 'error',
        title: 'Failed to create rule',
        message: error.message,
      });
    },
  });
};

export const useUpdateRule = () => {
  const queryClient = useQueryClient();
  const addNotification = useUIStore((state) => state.addNotification);

  return useMutation({
    mutationFn: ({ ruleId, data }: { ruleId: number; data: RuleUpdate }) =>
      rules.update(ruleId, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: [RULES_KEY, variables.ruleId] });
      queryClient.invalidateQueries({ queryKey: [RULES_KEY] });
      addNotification({
        type: 'success',
        title: 'Rule updated',
        message: 'Rule has been updated',
      });
    },
    onError: (error: any) => {
      addNotification({
        type: 'error',
        title: 'Failed to update rule',
        message: error.message,
      });
    },
  });
};

export const useDeleteRule = () => {
  const queryClient = useQueryClient();
  const addNotification = useUIStore((state) => state.addNotification);

  return useMutation({
    mutationFn: (ruleId: number) => rules.delete(ruleId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [RULES_KEY] });
      addNotification({
        type: 'success',
        title: 'Rule deleted',
        message: 'Rule has been deleted',
      });
    },
    onError: (error: any) => {
      addNotification({
        type: 'error',
        title: 'Failed to delete rule',
        message: error.message,
      });
    },
  });
};

export const useToggleRule = () => {
  const queryClient = useQueryClient();
  const addNotification = useUIStore((state) => state.addNotification);

  return useMutation({
    mutationFn: (ruleId: number) => rules.toggle(ruleId),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: [RULES_KEY, data.id] });
      queryClient.invalidateQueries({ queryKey: [RULES_KEY] });
      addNotification({
        type: 'success',
        title: data.is_active ? 'Rule enabled' : 'Rule disabled',
        message: `Rule is now ${data.is_active ? 'enabled' : 'disabled'}`,
      });
    },
    onError: (error: any) => {
      addNotification({
        type: 'error',
        title: 'Failed to toggle rule',
        message: error.message,
      });
    },
  });
};
