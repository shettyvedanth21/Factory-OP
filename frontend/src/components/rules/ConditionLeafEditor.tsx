// Condition Leaf Editor - Single condition row
import { ConditionLeaf, DeviceParameter } from '../../types';

interface ConditionLeafEditorProps {
  condition: ConditionLeaf;
  parameters: DeviceParameter[];
  onChange: (condition: ConditionLeaf) => void;
  onRemove: () => void;
}

const operatorOptions = [
  { value: 'gt', label: 'is greater than' },
  { value: 'lt', label: 'is less than' },
  { value: 'gte', label: 'is greater than or equal to' },
  { value: 'lte', label: 'is less than or equal to' },
  { value: 'eq', label: 'equals' },
  { value: 'neq', label: 'does not equal' },
];

export const ConditionLeafEditor = ({
  condition,
  parameters,
  onChange,
  onRemove,
}: ConditionLeafEditorProps) => {
  return (
    <div className="flex items-center gap-3 bg-gray-50 p-3 rounded-lg">
      {/* Parameter Dropdown */}
      <select
        value={condition.parameter}
        onChange={(e) => onChange({ ...condition, parameter: e.target.value })}
        className="flex-1 border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
      >
        <option value="">Select parameter...</option>
        {parameters.map((param) => (
          <option key={param.parameter_key} value={param.parameter_key}>
            {param.display_name || param.parameter_key}
            {param.unit ? ` (${param.unit})` : ''}
          </option>
        ))}
      </select>

      {/* Operator Dropdown */}
      <select
        value={condition.operator}
        onChange={(e) => onChange({ ...condition, operator: e.target.value as ConditionLeaf['operator'] })}
        className="w-48 border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
      >
        {operatorOptions.map((opt) => (
          <option key={opt.value} value={opt.value}>
            {opt.label}
          </option>
        ))}
      </select>

      {/* Value Input */}
      <input
        type="number"
        step="any"
        value={condition.value}
        onChange={(e) => onChange({ ...condition, value: parseFloat(e.target.value) || 0 })}
        className="w-32 border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        placeholder="Value"
      />

      {/* Remove Button */}
      <button
        onClick={onRemove}
        className="text-red-500 hover:text-red-700 p-2 rounded-md hover:bg-red-50 transition-colors"
        title="Remove condition"
      >
        <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
          <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
        </svg>
      </button>
    </div>
  );
};
