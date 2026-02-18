// Login Page
import { useState, useEffect } from 'react';
import { useSearchParams, useNavigate, Link } from 'react-router-dom';
import { useLogin } from '../hooks/useAuth';
import { Factory } from '../types';

const Login = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const factoryId = searchParams.get('factory_id');
  const login = useLogin();
  
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [factory, setFactory] = useState<Factory | null>(null);

  useEffect(() => {
    const stored = sessionStorage.getItem('selectedFactory');
    if (stored) {
      const parsed = JSON.parse(stored);
      if (parsed.id.toString() === factoryId) {
        setFactory(parsed);
      }
    } else {
      // No factory selected, redirect to factory select
      navigate('/factory-select');
    }
  }, [factoryId, navigate]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!factoryId) return;
    
    login.mutate({
      factory_id: parseInt(factoryId),
      email,
      password,
    });
  };

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
      <div className="max-w-md w-full">
        <div className="bg-white rounded-lg shadow-md p-8">
          <div className="text-center mb-8">
            <h1 className="text-2xl font-bold text-gray-900 mb-2">FactoryOps AI</h1>
            {factory && (
              <div className="text-gray-600">
                <p className="text-sm">Logging into</p>
                <p className="font-semibold text-lg text-blue-600">{factory.name}</p>
              </div>
            )}
          </div>

          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1">
                Email
              </label>
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="admin@vpc.com"
                required
              />
            </div>

            <div>
              <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-1">
                Password
              </label>
              <input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="••••••••"
                required
              />
            </div>

            <button
              type="submit"
              disabled={login.isPending}
              className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {login.isPending ? 'Logging in...' : 'Login'}
            </button>
          </form>

          <div className="mt-6 text-center">
            <Link
              to="/factory-select"
              className="text-sm text-blue-600 hover:text-blue-800"
            >
              ← Back to factory selection
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Login;
