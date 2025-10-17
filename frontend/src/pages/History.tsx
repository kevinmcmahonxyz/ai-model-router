import { useEffect, useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, Filter, ChevronLeft, ChevronRight } from 'lucide-react';
import apiClient from '../services/api';
import type { RequestListResponse, ModelInfo } from '../types';

export default function History() {
  const navigate = useNavigate();
  
  // State for request data
  const [data, setData] = useState<RequestListResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // State for filters
  const [searchInput, setSearchInput] = useState(''); // What user types
  const [debouncedSearch, setDebouncedSearch] = useState(''); // What we actually search
  const [selectedModel, setSelectedModel] = useState('');
  const [selectedStatus, setSelectedStatus] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [availableModels, setAvailableModels] = useState<ModelInfo[]>([]);

  // Debounce search input
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearch(searchInput);
      setCurrentPage(1); // Reset to page 1 when search changes
    }, 500); // Wait 500ms after user stops typing

    return () => clearTimeout(timer);
  }, [searchInput]);

  // Fetch available models for filter dropdown
  useEffect(() => {
    const fetchModels = async () => {
      try {
        const response = await apiClient.get('/v1/analytics/models');
        setAvailableModels(response.data);
      } catch (err) {
        console.error('Failed to fetch models:', err);
      }
    };
    fetchModels();
  }, []);

  // Fetch requests whenever filters change
  useEffect(() => {
    const fetchRequests = async () => {
      setLoading(true);
      try {
        const params = new URLSearchParams({
          page: currentPage.toString(),
          per_page: '20',
        });

        if (debouncedSearch) params.append('search', debouncedSearch); // Use debounced value
        if (selectedModel) params.append('model', selectedModel);
        if (selectedStatus) params.append('status', selectedStatus);

        const response = await apiClient.get(`/v1/analytics/requests?${params}`);
        setData(response.data);
        setLoading(false);
      } catch (err: any) {
        setError(err.response?.data?.detail || 'Failed to load requests');
        setLoading(false);
      }
    };

    fetchRequests();
  }, [currentPage, debouncedSearch, selectedModel, selectedStatus]); // Use debounced value

  // Reset to page 1 when filters change
  const handleFilterChange = () => {
    if (currentPage !== 1) {
      setCurrentPage(1);
    }
  };

  const handleModelChange = (value: string) => {
    setSelectedModel(value);
    handleFilterChange();
  };

  const handleStatusChange = (value: string) => {
    setSelectedStatus(value);
    handleFilterChange();
  };

  const handleRequestClick = (id: string) => {
    navigate(`/requests/${id}`);
  };

  if (loading && !data) {
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

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-gray-900">Request History</h2>
        <div className="text-sm text-gray-600">
          {data?.total.toLocaleString()} total requests
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-lg shadow p-4 mb-6">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2 text-gray-700">
            <Filter className="h-5 w-5" />
            <span className="font-medium">Filters:</span>
          </div>

          {/* Search */}
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search prompts..."
              value={searchInput} // Use searchInput, not debouncedSearch
              onChange={(e) => setSearchInput(e.target.value)} // Just update input
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>

          {/* Model Filter */}
          <select
            value={selectedModel}
            onChange={(e) => handleModelChange(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="">All Models</option>
            {availableModels.map((model) => (
              <option key={model.model_id} value={model.model_id}>
                {model.display_name}
              </option>
            ))}
          </select>

          {/* Status Filter */}
          <select
            value={selectedStatus}
            onChange={(e) => handleStatusChange(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="">All Status</option>
            <option value="success">Success</option>
            <option value="error">Error</option>
          </select>

          {/* Clear Filters */}
          {(searchInput || selectedModel || selectedStatus) && (
            <button
              onClick={() => {
                setSearchInput('');
                setDebouncedSearch('');
                setSelectedModel('');
                setSelectedStatus('');
                setCurrentPage(1);
              }}
              className="px-4 py-2 text-sm text-gray-600 hover:text-gray-900"
            >
              Clear
            </button>
          )}
        </div>
      </div>

      {/* Results */}
      {data && data.requests.length === 0 ? (
        <div className="bg-white rounded-lg shadow p-12 text-center">
          <p className="text-gray-500">No requests found</p>
        </div>
      ) : (
        <>
          {/* Table */}
          <div className="bg-white rounded-lg shadow overflow-hidden">
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Time
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Model
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Provider
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Prompt
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Tokens
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Cost
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Latency
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Status
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {data?.requests.map((request) => (
                    <tr
                      key={request.id}
                      onClick={() => handleRequestClick(request.id)}
                      className="hover:bg-gray-50 cursor-pointer"
                    >
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                        {new Date(request.created_at).toLocaleString()}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                        {request.model}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600 capitalize">
                        {request.provider}
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-600 max-w-md truncate">
                        {request.prompt_preview}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                        {request.input_tokens} / {request.output_tokens}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                        ${request.total_cost_usd.toFixed(6)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                        {request.latency_ms}ms
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span
                          className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                            request.status === 'success'
                              ? 'bg-green-100 text-green-800'
                              : 'bg-red-100 text-red-800'
                          }`}
                        >
                          {request.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Pagination */}
          {data && data.total_pages > 1 && (
            <div className="bg-white rounded-lg shadow px-6 py-4 mt-6">
              <div className="flex items-center justify-between">
                <div className="text-sm text-gray-600">
                  Showing page {data.page} of {data.total_pages}
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
                    disabled={currentPage === 1}
                    className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <ChevronLeft className="h-4 w-4 mr-1" />
                    Previous
                  </button>
                  <div className="text-sm text-gray-600">
                    Page {currentPage}
                  </div>
                  <button
                    onClick={() => setCurrentPage(Math.min(data.total_pages, currentPage + 1))}
                    disabled={currentPage === data.total_pages}
                    className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Next
                    <ChevronRight className="h-4 w-4 ml-1" />
                  </button>
                </div>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}