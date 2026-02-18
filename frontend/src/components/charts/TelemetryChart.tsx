// Telemetry Chart Component using Recharts
import { useState, useMemo } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import { useKPIHistory } from '../../hooks/useKPIs';
import { DeviceParameter } from '../../types';

interface TelemetryChartProps {
  deviceId: number;
  parameters: DeviceParameter[];
}

type TimeRange = '1H' | '24H' | '7D' | '30D';
type Interval = 'auto' | '1m' | '5m' | '1h' | '1d';

const TelemetryChart = ({ deviceId, parameters }: TelemetryChartProps) => {
  const [selectedParameter, setSelectedParameter] = useState<string>('');
  const [timeRange, setTimeRange] = useState<TimeRange>('24H');
  const [interval, setInterval] = useState<Interval>('auto');

  // Get KPI parameters only
  const kpiParameters = useMemo(() => {
    return parameters.filter((p) => p.is_kpi_selected);
  }, [parameters]);

  // Calculate start and end dates based on time range
  const { start, end } = useMemo(() => {
    const end = new Date();
    const start = new Date();
    
    switch (timeRange) {
      case '1H':
        start.setHours(end.getHours() - 1);
        break;
      case '24H':
        start.setDate(end.getDate() - 1);
        break;
      case '7D':
        start.setDate(end.getDate() - 7);
        break;
      case '30D':
        start.setDate(end.getDate() - 30);
        break;
    }
    
    return { start, end };
  }, [timeRange]);

  // Fetch history data
  const { data, isLoading } = useKPIHistory(deviceId, {
    parameter: selectedParameter,
    start: start.toISOString(),
    end: end.toISOString(),
    interval: interval === 'auto' ? undefined : interval,
  });

  // Format timestamp for X axis based on time range
  const formatXAxis = (timestamp: string) => {
    const date = new Date(timestamp);
    switch (timeRange) {
      case '1H':
        return date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
      case '24H':
        return date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
      case '7D':
        return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
      case '30D':
        return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
      default:
        return timestamp;
    }
  };

  // Format tooltip timestamp
  const formatTooltip = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    });
  };

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex flex-wrap gap-4 mb-6">
        {/* Parameter Selector */}
        <div className="flex-1 min-w-[200px]">
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Parameter
          </label>
          <select
            value={selectedParameter}
            onChange={(e) => setSelectedParameter(e.target.value)}
            className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">Select a parameter</option>
            {kpiParameters.map((param) => (
              <option key={param.parameter_key} value={param.parameter_key}>
                {param.display_name || param.parameter_key} ({param.unit})
              </option>
            ))}
          </select>
        </div>

        {/* Time Range Selector */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Time Range
          </label>
          <div className="flex rounded-md shadow-sm">
            {(['1H', '24H', '7D', '30D'] as TimeRange[]).map((range) => (
              <button
                key={range}
                onClick={() => setTimeRange(range)}
                className={`px-4 py-2 text-sm font-medium border ${
                  timeRange === range
                    ? 'bg-blue-600 text-white border-blue-600'
                    : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
                } ${range === '1H' ? 'rounded-l-md' : ''} ${range === '30D' ? 'rounded-r-md' : ''}`}
              >
                {range}
              </button>
            ))}
          </div>
        </div>

        {/* Interval Selector */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Interval
          </label>
          <select
            value={interval}
            onChange={(e) => setInterval(e.target.value as Interval)}
            className="border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="auto">Auto</option>
            <option value="1m">1 minute</option>
            <option value="5m">5 minutes</option>
            <option value="1h">1 hour</option>
            <option value="1d">1 day</option>
          </select>
        </div>
      </div>

      {/* Chart */}
      {isLoading ? (
        <div className="h-96 flex items-center justify-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        </div>
      ) : !selectedParameter ? (
        <div className="h-96 flex items-center justify-center text-gray-500">
          Select a parameter to view telemetry history
        </div>
      ) : !data?.points || data.points.length === 0 ? (
        <div className="h-96 flex items-center justify-center text-gray-500">
          No data available for the selected range
        </div>
      ) : (
        <div className="h-96">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={data.points}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis
                dataKey="timestamp"
                tickFormatter={formatXAxis}
                stroke="#6b7280"
                tick={{ fill: '#6b7280', fontSize: 12 }}
              />
              <YAxis
                stroke="#6b7280"
                tick={{ fill: '#6b7280', fontSize: 12 }}
                label={{
                  value: data.unit,
                  angle: -90,
                  position: 'insideLeft',
                  fill: '#6b7280',
                }}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#fff',
                  border: '1px solid #e5e7eb',
                  borderRadius: '6px',
                  padding: '12px',
                }}
                labelFormatter={(value) => formatTooltip(value as string)}
                formatter={(value: number) => [value.toFixed(2), data.display_name || data.parameter_key]}
              />
              <Line
                type="monotone"
                dataKey="value"
                stroke="#2563eb"
                strokeWidth={2}
                dot={false}
                activeDot={{ r: 6, fill: '#2563eb' }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
};

export default TelemetryChart;
