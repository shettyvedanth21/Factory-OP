// Factory Select Page
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { auth } from '../api/endpoints';
import { Factory } from '../types';

const FactorySelect = () => {
  const navigate = useNavigate();
  
  const { data: factories, isLoading, error } = useQuery({
    queryKey: ['factories'],
    queryFn: () => auth.listFactories(),
  });

  const handleFactorySelect = (factory: Factory) => {
    sessionStorage.setItem('selectedFactory', JSON.stringify(factory));
    navigate(`/login?factory_id=${factory.id}`);
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading factories...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="text-red-500 text-xl mb-4">Error loading factories</div>
          <p className="text-gray-600">Please try again later</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
      <div className="max-w-4xl w-full">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">FactoryOps AI</h1>
          <p className="text-gray-600">Select a factory to continue</p>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {factories?.map((factory) => (
            <button
              key={factory.id}
              onClick={() => handleFactorySelect(factory)}
              className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow text-left border border-gray-200 hover:border-blue-500"
            >
              <div className="flex items-center space-x-4">
                <div className="h-12 w-12 bg-blue-100 rounded-full flex items-center justify-center">
                  <span className="text-blue-600 font-bold text-lg">
                    {factory.name.charAt(0)}
                  </span>
                </div>
                <div>
                  <h3 className="font-semibold text-gray-900">{factory.name}</h3>
                  <p className="text-sm text-gray-500">{factory.slug}</p>
                </div>
              </div>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};

export default FactorySelect;
