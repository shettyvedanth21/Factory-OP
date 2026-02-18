// Rule Builder Page
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useCreateRule } from '../hooks/useRules';
import { RuleCreate } from '../types';

const RuleBuilder = () => {
  const navigate = useNavigate();
  const createRule = useCreateRule();
  const [formData, setFormData] = useState<Partial<RuleCreate>>({
    name: '',
    scope: 'device',
    device_ids: [],
    conditions: {
      operator: 'AND',
      conditions: [{ parameter: '', operator: 'gt', value: 0 }],
    },
    cooldown_minutes: 15,
    severity: 'medium',
    schedule_type: 'always',
    notification_channels: { email: false, whatsapp: false },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    createRule.mutate(formData as RuleCreate, {
      onSuccess: () => navigate('/rules'),
    });
  };

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Create Rule</h1>
      
      <form onSubmit={handleSubmit} className="bg-white rounded-lg shadow p-6 max-w-2xl">
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">Name</label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm p-2"
              required
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700">Severity</label>
            <select
              value={formData.severity}
              onChange={(e) => setFormData({ ...formData, severity: e.target.value as any })}
              className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm p-2"
            >
              <option value="low">Low</option>
              <option value="medium">Medium</option>
              <option value="high">High</option>
              <option value="critical">Critical</option>
            </select>
          </div>
          
          <button
            type="submit"
            disabled={createRule.isPending}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50"
          >
            {createRule.isPending ? 'Creating...' : 'Create Rule'}
          </button>
        </div>
      </form>
    </div>
  );
};

export default RuleBuilder;
