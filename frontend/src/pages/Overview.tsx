import { useEffect, useState } from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend, LineChart, Line, XAxis, YAxis, CartesianGrid } from 'recharts';
import apiClient from '../services/api';
import type { UsageStats } from '../types';

export default function Overview() {
  const [stats, setStats] = useState<UsageStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const response = await apiClient.get('/v1/analytics/usage?days=30');
        setStats(response.data);
        setLoading(false);
      } catch (err: any) {
        setError(err.response?.data?.detail || 'Failed to load data');
        setLoading(false);
      }
    };

    fetchStats();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">Loading...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <p className="text-red-800">Error: {error}</p>
      </div>
    );
  }

  if (!stats) {
    return (
      <div className="text-center text-gray-500">No data available</div>
    );
  }

  // Calculate per-request metrics
  const avgCostPerRequest = stats.total_requests > 0 
    ? stats.total_cost_usd / stats.total_requests 
    : 0;

  // Colors for charts
  const PROVIDER_COLORS = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444'];

  // Prepare data for pie chart (providers)
  const providerChartData = stats.by_provider.map((p) => ({
    name: p.provider.charAt(0).toUpperCase() + p.provider.slice(1),
    value: parseFloat(p.cost_usd.toFixed(6)),
    requests: p.requests,
  }));

  // Prepare data for line chart (daily trends)
  const dailyChartData = stats.daily_stats.map((d) => ({
    date: new Date(d.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
    requests: d.requests,
    cost: parseFloat(d.cost_usd.toFixed(6)),
  }));

  return (
    <div>
      <h2 className="text-2xl font-bold text-gray-900 mb-6">Overview</h2>
      
      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <div className="bg-white rounded-lg shadow p-6">
          <p className="text-sm text-gray-600 mb-1">Total Requests</p>
          <p className="text-3xl font-bold text-gray-900">
            {stats.total_requests.toLocaleString()}
          </p>
        </div>
        
        <div className="bg-white rounded-lg shadow p-6">
          <p className="text-sm text-gray-600 mb-1">Total Cost</p>
          <p className="text-3xl font-bold text-gray-900">
            ${stats.total_cost_usd.toFixed(4)}
          </p>
        </div>
        
        <div className="bg-white rounded-lg shadow p-6">
          <p className="text-sm text-gray-600 mb-1">Avg Cost/Request</p>
          <p className="text-3xl font-bold text-gray-900">
            ${avgCostPerRequest.toFixed(6)}
          </p>
        </div>
        
        <div className="bg-white rounded-lg shadow p-6">
          <p className="text-sm text-gray-600 mb-1">Success Rate</p>
          <p className="text-3xl font-bold text-gray-900">
            {(stats.success_rate * 100).toFixed(1)}%
          </p>
        </div>
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        {/* Provider Pie Chart */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Cost by Provider
          </h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={providerChartData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={(entry: any) => `${entry.name} ${(entry.percent * 100).toFixed(0)}%`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {providerChartData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={PROVIDER_COLORS[index % PROVIDER_COLORS.length]} />
                ))}
              </Pie>
              <Tooltip 
                formatter={(value: any) => `$${Number(value).toFixed(6)}`}
              />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Daily Usage Line Chart */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Daily Usage Trend
          </h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={dailyChartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis yAxisId="left" />
              <YAxis yAxisId="right" orientation="right" />
              <Tooltip />
              <Legend />
              <Line 
                yAxisId="left"
                type="monotone" 
                dataKey="requests" 
                stroke="#3B82F6" 
                strokeWidth={2}
                name="Requests"
              />
              <Line 
                yAxisId="right"
                type="monotone" 
                dataKey="cost" 
                stroke="#10B981" 
                strokeWidth={2}
                name="Cost ($)"
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Per-Model Metrics Table */}
      <div className="bg-white rounded-lg shadow p-6 mb-8">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          Cost Per Request by Model
        </h3>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Model
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Requests
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Total Cost
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Avg Cost/Request
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  % of Total Cost
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {stats.by_model.map((model) => {
                const avgCost = model.requests > 0 ? model.cost_usd / model.requests : 0;
                const percentOfTotal = stats.total_cost_usd > 0 
                  ? (model.cost_usd / stats.total_cost_usd) * 100 
                  : 0;
                
                return (
                  <tr key={model.model} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {model.model}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                      {model.requests.toLocaleString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                      ${model.cost_usd.toFixed(6)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-semibold text-gray-900">
                      ${avgCost.toFixed(6)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                      {percentOfTotal.toFixed(1)}%
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Provider Breakdown with Progress Bars */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          Provider Usage Details
        </h3>
        <div className="space-y-4">
          {stats.by_provider.map((provider, index) => {
            const avgCost = provider.requests > 0 ? provider.cost_usd / provider.requests : 0;
            const percentOfTotal = stats.total_cost_usd > 0 
              ? (provider.cost_usd / stats.total_cost_usd) * 100 
              : 0;
            
            return (
              <div key={provider.provider} className="border-l-4 pl-4" style={{ borderColor: PROVIDER_COLORS[index] }}>
                <div className="flex items-center justify-between mb-2">
                  <div>
                    <span className="text-sm font-semibold text-gray-900 capitalize">
                      {provider.provider}
                    </span>
                    <span className="text-xs text-gray-500 ml-2">
                      {provider.requests} requests
                    </span>
                  </div>
                  <div className="text-right">
                    <div className="text-sm font-medium text-gray-900">
                      ${provider.cost_usd.toFixed(6)}
                    </div>
                    <div className="text-xs text-gray-500">
                      ${avgCost.toFixed(6)}/req
                    </div>
                  </div>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="h-2 rounded-full"
                    style={{
                      width: `${percentOfTotal}%`,
                      backgroundColor: PROVIDER_COLORS[index],
                    }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}