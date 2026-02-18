// Device Detail Page
import { useParams } from 'react-router-dom';
import { useDevice } from '../hooks/useDevices';
import { useKPIsLive } from '../hooks/useKPIs';

const DeviceDetail = () => {
  const { deviceId } = useParams<{ deviceId: string }>();
  const { data: device } = useDevice(parseInt(deviceId || '0'));
  const { data: kpis } = useKPIsLive(parseInt(deviceId || '0'));

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 mb-6">
        {device?.name || device?.device_key}
      </h1>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {kpis?.kpis?.map((kpi) => (
          <div key={kpi.parameter_key} className="bg-white rounded-lg shadow p-6">
            <h3 className="text-sm font-medium text-gray-500">
              {kpi.display_name || kpi.parameter_key}
            </h3>
            <p className="text-3xl font-bold text-gray-900 mt-2">
              {kpi.value.toFixed(2)}
              <span className="text-sm font-normal text-gray-500 ml-1">
                {kpi.unit}
              </span>
            </p>
            {kpi.is_stale && (
              <span className="text-xs text-yellow-600">Stale data</span>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

export default DeviceDetail;
