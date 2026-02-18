// Rule Builder Page - Create/Edit rules with 4-step form
import { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useDevices } from '../hooks/useDevices';
import { useRule, useCreateRule, useUpdateRule } from '../hooks/useRules';
import { ConditionGroupEditor } from '../components/rules/ConditionGroupEditor';
import { parameters } from '../api/endpoints';
import {
  RuleCreate,
  RuleUpdate,
  ConditionTree,
  DeviceParameter,
  DeviceListItem,
} from '../types';

const severityOptions = [
  { value: 'low', label: 'Low', color: 'bg-blue-100 text-blue-800 border-blue-300' },
  { value: 'medium', label: 'Medium', color: 'bg-yellow-100 text-yellow-800 border-yellow-300' },
  { value: 'high', label: 'High', color: 'bg-orange-100 text-orange-800 border-orange-300' },
  { value: 'critical', label: 'Critical', color: 'bg-red-100 text-red-800 border-red-300' },
];

const scheduleTypeOptions = [
  { value: 'always', label: 'Always Active' },
  { value: 'time_window', label: 'Time Window (Daily)' },
  { value: 'date_range', label: 'Date Range' },
];

const weekDays = [
  { value: 1, label: 'Mon' },
  { value: 2, label: 'Tue' },
  { value: 3, label: 'Wed' },
  { value: 4, label: 'Thu' },
  { value: 5, label: 'Fri' },
  { value: 6, label: 'Sat' },
  { value: 0, label: 'Sun' },
];

const operatorLabels: Record<string, string> = {
  gt: 'is greater than',
  lt: 'is less than',
  gte: 'is greater than or equal to',
  lte: 'is less than or equal to',
  eq: 'equals',
  neq: 'does not equal',
};

const buildConditionPreview = (conditions: ConditionTree): string => {
  const operator = conditions.operator === 'AND' ? ' AND ' : ' OR ';
  const parts = conditions.conditions.map((cond: any) => {
    if ('conditions' in cond) {
      return `(${buildConditionPreview(cond)})`;
    }
    return `${cond.parameter} ${operatorLabels[cond.operator] || cond.operator} ${cond.value}`;
  });
  return parts.join(operator);
};

const initialConditionTree: ConditionTree = {
  operator: 'AND',
  conditions: [
    {
      parameter: '',
      operator: 'gt',
      value: 0,
    },
  ],
};

const RuleBuilder = () => {
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const isEditMode = !!id;
  const ruleId = id ? parseInt(id, 10) : undefined;

  const { data: existingRule, isLoading: isLoadingRule } = useRule(ruleId || 0);
  const { data: devicesData } = useDevices({ per_page: 100 });

  const [currentStep, setCurrentStep] = useState(1);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});

  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [severity, setSeverity] = useState<'low' | 'medium' | 'high' | 'critical'>('medium');

  const [scope, setScope] = useState<'device' | 'global'>('device');
  const [selectedDeviceIds, setSelectedDeviceIds] = useState<number[]>([]);
  const [deviceSearch, setDeviceSearch] = useState('');
  const [availableParameters, setAvailableParameters] = useState<DeviceParameter[]>([]);
  const [isLoadingParameters, setIsLoadingParameters] = useState(false);

  const [conditions, setConditions] = useState<ConditionTree>(initialConditionTree);

  const [scheduleType, setScheduleType] = useState<'always' | 'time_window' | 'date_range'>('always');
  const [scheduleConfig, setScheduleConfig] = useState<{
    start_time?: string;
    end_time?: string;
    days?: number[];
    start_date?: string;
    end_date?: string;
  }>({});
  const [cooldownMinutes, setCooldownMinutes] = useState(15);
  const [notificationChannels, setNotificationChannels] = useState({
    email: true,
    whatsapp: false,
  });

  const createRule = useCreateRule();
  const updateRule = useUpdateRule();

  useEffect(() => {
    if (existingRule && isEditMode) {
      setName(existingRule.name);
      setDescription(existingRule.description || '');
      setSeverity(existingRule.severity);
      setScope(existingRule.scope);
      setSelectedDeviceIds(existingRule.device_ids || []);
      setConditions(existingRule.conditions);
      setScheduleType(existingRule.schedule_type);
      setScheduleConfig(existingRule.schedule_config || {});
      setCooldownMinutes(existingRule.cooldown_minutes);
      setNotificationChannels(existingRule.notification_channels || { email: true, whatsapp: false });
    }
  }, [existingRule, isEditMode]);

  useEffect(() => {
    const loadParameters = async () => {
      if (selectedDeviceIds.length === 0) {
        setAvailableParameters([]);
        return;
      }

      setIsLoadingParameters(true);
      const allParams: DeviceParameter[] = [];
      const seenKeys = new Set<string>();

      try {
        for (const deviceId of selectedDeviceIds) {
          const deviceParams = await parameters.list(deviceId);
          deviceParams.forEach((param) => {
            if (!seenKeys.has(param.parameter_key)) {
              seenKeys.add(param.parameter_key);
              allParams.push(param);
            }
          });
        }
        setAvailableParameters(allParams);
      } catch (error) {
        console.error('Failed to load parameters:', error);
      } finally {
        setIsLoadingParameters(false);
      }
    };

    loadParameters();
  }, [selectedDeviceIds]);

  const validateStep = (step: number): boolean => {
    const newErrors: Record<string, string> = {};

    if (step === 1) {
      if (!name.trim()) {
        newErrors.name = 'Rule name is required';
      }
    }

    if (step === 2) {
      if (scope === 'device' && selectedDeviceIds.length === 0) {
        newErrors.devices = 'At least one device must be selected';
      }
    }

    if (step === 3) {
      const hasValidConditions = conditions.conditions.length > 0 &&
        conditions.conditions.every((cond: any) => {
          if ('conditions' in cond) return true;
          return cond.parameter && cond.operator && !isNaN(cond.value);
        });
      
      if (!hasValidConditions) {
        newErrors.conditions = 'At least one valid condition is required';
      }
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleNext = () => {
    if (validateStep(currentStep)) {
      setCurrentStep((s) => Math.min(s + 1, 4));
    }
  };

  const handleBack = () => {
    setCurrentStep((s) => Math.max(s - 1, 1));
  };

  const handleSubmit = async () => {
    if (!validateStep(currentStep)) return;

    setIsSubmitting(true);

    const ruleData: RuleCreate = {
      name: name.trim(),
      description: description.trim() || undefined,
      scope,
      device_ids: scope === 'device' ? selectedDeviceIds : [],
      conditions,
      cooldown_minutes: cooldownMinutes,
      severity,
      schedule_type: scheduleType,
      ...(scheduleType !== 'always' && { schedule_config: scheduleConfig }),
      notification_channels: notificationChannels,
    };

    try {
      if (isEditMode && ruleId) {
        await updateRule.mutateAsync({ ruleId, data: ruleData as RuleUpdate });
      } else {
        await createRule.mutateAsync(ruleData);
      }
      navigate('/rules');
    } catch (error) {
      console.error('Failed to save rule:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const filteredDevices = devicesData?.data?.filter((device: DeviceListItem) =>
    deviceSearch
      ? device.name?.toLowerCase().includes(deviceSearch.toLowerCase()) ||
        device.device_key.toLowerCase().includes(deviceSearch.toLowerCase())
      : true
  ) || [];

  if (isEditMode && isLoadingRule) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">
          {isEditMode ? 'Edit Rule' : 'Create New Rule'}
        </h1>
        <p className="text-gray-600 mt-1">
          {isEditMode ? 'Modify the rule configuration' : 'Set up automated alerts based on device telemetry'}
        </p>
      </div>

      <div className="mb-8">
        <div className="flex items-center justify-between">
          {[1, 2, 3, 4].map((step, index) => (
            <div key={step} className="flex items-center flex-1">
              <div
                className={`flex items-center justify-center w-10 h-10 rounded-full font-semibold ${
                  currentStep >= step
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-200 text-gray-600'
                }`}
              >
                {currentStep > step ? (
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                ) : (
                  step
                )}
              </div>
              <div className="ml-3 hidden sm:block">
                <div className={`text-sm font-medium ${currentStep >= step ? 'text-gray-900' : 'text-gray-500'}`}>
                  {step === 1 && 'Basic Info'}
                  {step === 2 && 'Scope & Devices'}
                  {step === 3 && 'Conditions'}
                  {step === 4 && 'Schedule & Notifications'}
                </div>
              </div>
              {index < 3 && (
                <div className={`flex-1 h-1 mx-4 ${currentStep > step ? 'bg-blue-600' : 'bg-gray-200'}`} />
              )}
            </div>
          ))}
        </div>
      </div>

      <div className="bg-white rounded-lg shadow p-6">
        {currentStep === 1 && (
          <div className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Rule Name <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className={`w-full border rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                  errors.name ? 'border-red-500' : 'border-gray-300'
                }`}
                placeholder="e.g., High Voltage Alert"
              />
              {errors.name && <p className="mt-1 text-sm text-red-600">{errors.name}</p>}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Description</label>
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                rows={3}
                className="w-full border border-gray-300 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Optional description..."
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Severity</label>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                {severityOptions.map((option) => (
                  <button
                    key={option.value}
                    onClick={() => setSeverity(option.value as typeof severity)}
                    className={`px-4 py-3 rounded-lg border-2 text-center transition-colors ${
                      severity === option.value
                        ? option.color + ' border-current'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    {option.label}
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}

        {currentStep === 2 && (
          <div className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Rule Scope</label>
              <div className="flex gap-4">
                <button
                  onClick={() => setScope('device')}
                  className={`flex-1 px-4 py-4 rounded-lg border-2 text-center transition-colors ${
                    scope === 'device'
                      ? 'border-blue-600 bg-blue-50'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  <div className="font-medium text-gray-900">Device-Specific</div>
                  <div className="text-sm text-gray-500 mt-1">Apply to selected devices only</div>
                </button>
                <button
                  onClick={() => setScope('global')}
                  className={`flex-1 px-4 py-4 rounded-lg border-2 text-center transition-colors ${
                    scope === 'global'
                      ? 'border-blue-600 bg-blue-50'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  <div className="font-medium text-gray-900">Global</div>
                  <div className="text-sm text-gray-500 mt-1">Apply to all factory devices</div>
                </button>
              </div>
            </div>

            {scope === 'device' && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Select Devices <span className="text-red-500">*</span>
                </label>
                
                <div className="relative mb-4">
                  <input
                    type="text"
                    value={deviceSearch}
                    onChange={(e) => setDeviceSearch(e.target.value)}
                    placeholder="Search devices..."
                    className="w-full border border-gray-300 rounded-lg pl-10 pr-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                  <span className="absolute left-3 top-2.5 text-gray-400">🔍</span>
                </div>

                <div className={`border rounded-lg overflow-hidden ${errors.devices ? 'border-red-500' : 'border-gray-300'}`}>
                  <div className="max-h-64 overflow-y-auto">
                    {filteredDevices.map((device: DeviceListItem) => (
                      <label
                        key={device.id}
                        className="flex items-center p-3 hover:bg-gray-50 cursor-pointer border-b last:border-b-0"
                      >
                        <input
                          type="checkbox"
                          checked={selectedDeviceIds.includes(device.id)}
                          onChange={(e) => {
                            if (e.target.checked) {
                              setSelectedDeviceIds([...selectedDeviceIds, device.id]);
                            } else {
                              setSelectedDeviceIds(selectedDeviceIds.filter((id) => id !== device.id));
                            }
                          }}
                          className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                        />
                        <div className="ml-3 flex-1">
                          <div className="font-medium text-gray-900">{device.name || device.device_key}</div>
                          <div className="text-sm text-gray-500">{device.device_key}</div>
                        </div>
                      </label>
                    ))}
                  </div>
                </div>
                
                {errors.devices && <p className="mt-1 text-sm text-red-600">{errors.devices}</p>}
                <div className="mt-2 text-sm text-gray-600">
                  {selectedDeviceIds.length} device{selectedDeviceIds.length !== 1 ? 's' : ''} selected
                </div>
              </div>
            )}

            {scope === 'global' && (
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <p className="text-blue-800">
                  This rule will apply to <strong>all devices</strong> in your factory.
                </p>
              </div>
            )}
          </div>
        )}

        {currentStep === 3 && (
          <div className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Alert Conditions
              </label>
              
              {isLoadingParameters ? (
                <div className="text-center py-8">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
                  <p className="mt-2 text-sm text-gray-600">Loading parameters...</p>
                </div>
              ) : availableParameters.length === 0 ? (
                <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                  <p className="text-yellow-800">
                    No parameters available. Select devices that have reported telemetry data.
                  </p>
                </div>
              ) : (
                <>
                  <ConditionGroupEditor
                    group={conditions}
                    parameters={availableParameters}
                    onChange={setConditions}
                  />
                  {errors.conditions && (
                    <p className="mt-2 text-sm text-red-600">{errors.conditions}</p>
                  )}
                </>
              )}
            </div>

            <div className="bg-gray-50 rounded-lg p-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Preview
              </label>
              <p className="text-gray-800">
                Alert when <strong>{buildConditionPreview(conditions)}</strong>
              </p>
            </div>
          </div>
        )}

        {currentStep === 4 && (
          <div className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Schedule</label>
              <select
                value={scheduleType}
                onChange={(e) => setScheduleType(e.target.value as typeof scheduleType)}
                className="w-full border border-gray-300 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                {scheduleTypeOptions.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </div>

            {scheduleType === 'time_window' && (
              <div className="space-y-4 border border-gray-200 rounded-lg p-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Active Days</label>
                  <div className="flex flex-wrap gap-2">
                    {weekDays.map((day) => (
                      <button
                        key={day.value}
                        onClick={() => {
                          const currentDays = scheduleConfig.days || [];
                          const newDays = currentDays.includes(day.value)
                            ? currentDays.filter((d) => d !== day.value)
                            : [...currentDays, day.value];
                          setScheduleConfig({ ...scheduleConfig, days: newDays });
                        }}
                        className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                          (scheduleConfig.days || []).includes(day.value)
                            ? 'bg-blue-600 text-white'
                            : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                        }`}
                      >
                        {day.label}
                      </button>
                    ))}
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Start Time</label>
                    <input
                      type="time"
                      value={scheduleConfig.start_time || '08:00'}
                      onChange={(e) => setScheduleConfig({ ...scheduleConfig, start_time: e.target.value })}
                      className="w-full border border-gray-300 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">End Time</label>
                    <input
                      type="time"
                      value={scheduleConfig.end_time || '18:00'}
                      onChange={(e) => setScheduleConfig({ ...scheduleConfig, end_time: e.target.value })}
                      className="w-full border border-gray-300 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                </div>
              </div>
            )}

            {scheduleType === 'date_range' && (
              <div className="grid grid-cols-2 gap-4 border border-gray-200 rounded-lg p-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Start Date</label>
                  <input
                    type="date"
                    value={scheduleConfig.start_date || ''}
                    onChange={(e) => setScheduleConfig({ ...scheduleConfig, start_date: e.target.value })}
                    className="w-full border border-gray-300 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">End Date</label>
                  <input
                    type="date"
                    value={scheduleConfig.end_date || ''}
                    onChange={(e) => setScheduleConfig({ ...scheduleConfig, end_date: e.target.value })}
                    className="w-full border border-gray-300 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>
            )}

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Cooldown (minutes)
              </label>
              <input
                type="number"
                min={1}
                max={1440}
                value={cooldownMinutes}
                onChange={(e) => setCooldownMinutes(parseInt(e.target.value) || 15)}
                className="w-full border border-gray-300 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Notifications</label>
              <div className="space-y-3">
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={notificationChannels.email}
                    onChange={(e) => setNotificationChannels({ ...notificationChannels, email: e.target.checked })}
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                  <span className="ml-3 text-gray-700">Email notifications</span>
                </label>
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={notificationChannels.whatsapp}
                    onChange={(e) => setNotificationChannels({ ...notificationChannels, whatsapp: e.target.checked })}
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                  <span className="ml-3 text-gray-700">WhatsApp notifications</span>
                </label>
              </div>
            </div>
          </div>
        )}

        <div className="flex justify-between mt-8 pt-6 border-t border-gray-200">
          <button
            onClick={handleBack}
            disabled={currentStep === 1}
            className="px-6 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            ← Back
          </button>

          <div className="flex gap-3">
            <button
              onClick={() => navigate('/rules')}
              className="px-6 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50"
            >
              Cancel
            </button>

            {currentStep < 4 ? (
              <button
                onClick={handleNext}
                className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                Next →
              </button>
            ) : (
              <button
                onClick={handleSubmit}
                disabled={isSubmitting}
                className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isSubmitting ? 'Saving...' : isEditMode ? 'Save Changes' : 'Create Rule'}
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default RuleBuilder;
