// Condition Group Editor - Nested AND/OR groups
import { ConditionTree, ConditionLeaf, DeviceParameter } from '../../types';
import { ConditionLeafEditor } from './ConditionLeafEditor';

interface ConditionGroupEditorProps {
  group: ConditionTree;
  parameters: DeviceParameter[];
  onChange: (group: ConditionTree) => void;
  onRemove?: () => void;
  depth?: number;
}

const MAX_DEPTH = 2;

const createEmptyLeaf = (): ConditionLeaf => ({
  parameter: '',
  operator: 'gt',
  value: 0,
});

const createEmptyGroup = (): ConditionTree => ({
  operator: 'AND',
  conditions: [createEmptyLeaf()],
});

export const ConditionGroupEditor = ({
  group,
  parameters,
  onChange,
  onRemove,
  depth = 0,
}: ConditionGroupEditorProps) => {
  const canNest = depth < MAX_DEPTH;

  const updateOperator = (operator: 'AND' | 'OR') => {
    onChange({ ...group, operator });
  };

  const updateCondition = (index: number, condition: ConditionLeaf | ConditionTree) => {
    const newConditions = [...group.conditions];
    newConditions[index] = condition;
    onChange({ ...group, conditions: newConditions });
  };

  const removeCondition = (index: number) => {
    const newConditions = group.conditions.filter((_, i) => i !== index);
    onChange({ ...group, conditions: newConditions });
  };

  const addLeaf = () => {
    onChange({ ...group, conditions: [...group.conditions, createEmptyLeaf()] });
  };

  const addGroup = () => {
    if (!canNest) return;
    onChange({ ...group, conditions: [...group.conditions, createEmptyGroup()] });
  };

  const indentClass = depth === 0 ? '' : `ml-${Math.min(depth * 4, 8)}`;
  const borderClass = depth > 0 ? 'border-l-4 border-blue-200 pl-4' : '';

  return (
    <div className={`${indentClass} ${borderClass} space-y-3`}>
      {/* Group Header with AND/OR Toggle */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium text-gray-600">Match</span>
          <div className="inline-flex rounded-md shadow-sm" role="group">
            <button
              onClick={() => updateOperator('AND')}
              className={`px-4 py-2 text-sm font-medium rounded-l-lg border ${
                group.operator === 'AND'
                  ? 'bg-blue-600 text-white border-blue-600'
                  : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
              }`}
            >
              ALL (AND)
            </button>
            <button
              onClick={() => updateOperator('OR')}
              className={`px-4 py-2 text-sm font-medium rounded-r-lg border-t border-r border-b ${
                group.operator === 'OR'
                  ? 'bg-blue-600 text-white border-blue-600'
                  : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
              }`}
            >
              ANY (OR)
            </button>
          </div>
          <span className="text-sm text-gray-500">of the following:</span>
        </div>

        {onRemove && (
          <button
            onClick={onRemove}
            className="text-red-500 hover:text-red-700 text-sm font-medium"
          >
            Remove Group
          </button>
        )}
      </div>

      {/* Conditions List */}
      <div className="space-y-2">
        {group.conditions.map((condition, index) => {
          const isGroup = 'conditions' in condition;

          if (isGroup) {
            return (
              <ConditionGroupEditor
                key={index}
                group={condition as ConditionTree}
                parameters={parameters}
                onChange={(newGroup) => updateCondition(index, newGroup)}
                onRemove={() => removeCondition(index)}
                depth={depth + 1}
              />
            );
          }

          return (
            <ConditionLeafEditor
              key={index}
              condition={condition as ConditionLeaf}
              parameters={parameters}
              onChange={(newCondition) => updateCondition(index, newCondition)}
              onRemove={() => removeCondition(index)}
            />
          );
        })}
      </div>

      {/* Add Buttons */}
      <div className="flex gap-2">
        <button
          onClick={addLeaf}
          className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
        >
          <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 mr-1" viewBox="0 0 20 20" fill="currentColor">
            <path fillRule="evenodd" d="M10 3a1 1 0 011 1v5h5a1 1 0 110 2h-5v5a1 1 0 11-2 0v-5H4a1 1 0 110-2h5V4a1 1 0 011-1z" clipRule="evenodd" />
          </svg>
          Add Condition
        </button>

        {canNest && (
          <button
            onClick={addGroup}
            className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 mr-1" viewBox="0 0 20 20" fill="currentColor">
              <path d="M7 3a1 1 0 000 2h6a1 1 0 100-2H7zM4 7a1 1 0 011-1h10a1 1 0 110 2H5a1 1 0 01-1-1zM2 11a2 2 0 012-2h12a2 2 0 012 2v4a2 2 0 01-2 2H4a2 2 0 01-2-2v-4z" />
            </svg>
            Add Group
          </button>
        )}
      </div>
    </div>
  );
};
