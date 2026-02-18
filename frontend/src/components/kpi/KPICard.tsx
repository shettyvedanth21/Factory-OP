// KPI Card Component
import { useEffect, useState } from 'react';
import { KPIValue } from '../../types';

interface KPICardProps extends KPIValue {
  className?: string;
}

const KPICard = ({ 
  parameter_key, 
  display_name, 
  unit, 
  value, 
  is_stale,
  className = '' 
}: KPICardProps) => {
  const [displayValue, setDisplayValue] = useState(value);

  // Smooth transition when value changes
  useEffect(() => {
    setDisplayValue(value);
  }, [value]);

  // Format value based on type
  const formatValue = (val: number) => {
    // Check if it's likely an integer
    if (Number.isInteger(val) || Math.abs(val) > 100) {
      return val.toFixed(0);
    }
    return val.toFixed(2);
  };

  if (is_stale) {
    return (
      <div className={`bg-gray-100 rounded-lg shadow p-6 opacity-60 ${className}`}>
        <div className="border-t-4 border-gray-400 rounded-t-lg -mt-6 -mx-6 mb-4"></div>
        <h3 className="text-sm font-medium text-gray-500 uppercase tracking-wider">
          {display_name || parameter_key}
        </h3>
        <div className="mt-2">
          <span className="text-3xl font-bold text-gray-400">--</span>
          <span className="text-sm text-gray-400 ml-1">{unit}</span>
        </div>
        <p className="mt-2 text-xs text-gray-400">No data</p>
      </div>
    );
  }

  return (
    <div className={`bg-white rounded-lg shadow p-6 transition-all duration-500 ${className}`}>
      <div className="border-t-4 border-blue-500 rounded-t-lg -mt-6 -mx-6 mb-4"></div>
      <h3 className="text-sm font-medium text-gray-500 uppercase tracking-wider">
        {display_name || parameter_key}
      </h3>
      <div className="mt-2 transition-all duration-500">
        <span className="text-3xl font-bold text-gray-900 transition-all duration-500">
          {formatValue(displayValue)}
        </span>
        <span className="text-sm text-gray-500 ml-1">{unit}</span>
      </div>
    </div>
  );
};

export default KPICard;
