// KPI Card Grid Component
import { Link } from 'react-router-dom';
import { useKPIsLive } from '../../hooks/useKPIs';
import KPICard from './KPICard';

interface KPICardGridProps {
  deviceId: number;
}

const KPICardGrid = ({ deviceId }: KPICardGridProps) => {
  const { data, isLoading } = useKPIsLive(deviceId);

  if (isLoading) {
    return (
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="bg-white rounded-lg shadow p-6 animate-pulse">
            <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
            <div className="h-8 bg-gray-200 rounded w-1/2"></div>
          </div>
        ))}
      </div>
    );
  }

  if (!data?.kpis || data.kpis.length === 0) {
    return (
      <div className="bg-gray-50 rounded-lg p-8 text-center">
        <p className="text-gray-500 mb-4">No KPIs selected for this device</p>
        <Link 
          to={`/machines/${deviceId}`}
          className="text-blue-600 hover:text-blue-800 font-medium"
        >
          Select parameters to monitor →
        </Link>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
      {data.kpis.map((kpi) => (
        <KPICard key={kpi.parameter_key} {...kpi} />
      ))}
    </div>
  );
};

export default KPICardGrid;
