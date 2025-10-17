import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, Clock, DollarSign, Zap, CheckCircle, XCircle } from 'lucide-react';
import apiClient from '../services/api';
import type { RequestDetail } from '../types';

export default function RequestDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  
  const [request, setRequest] = useState<RequestDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchRequest = async () => {
      if (!id) return;
      
      try {
        const response = await apiClient.get(`/v1/analytics/requests/${id}`);
        setRequest(response.data);
        setLoading(false);
      } catch (err: any) {
        setError(err.response?.data?.detail || 'Failed to load request');
        setLoading(false);
      }
    };

    fetchRequest();
  }, [id]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">Loading...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div>
        <button
          onClick={() => navigate('/history')}
          className="inline-flex items-center text-blue-600 hover:text-blue-800 mb-6"
        >
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back to History
        </button>
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800">Error: {error}</p>
        </div>
      </div>
    );
  }

  if (!request) {
    return (
      <div className="text-center text-gray-500">Request not found</div>
    );
  }

  return (
    <div>
      {/* Back Button */}
      <button
        onClick={() => navigate('/history')}
        className="inline-flex items-center text-blue-600 hover:text-blue-800 mb-6"
      >
        <ArrowLeft className="h-4 w-4 mr-2" />
        Back to History
      </button>

      {/* Header */}
      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <div className="flex items-start justify-between mb-4">
          <div>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">Request Detail</h2>
            <p className="text-sm text-gray-600">ID: {request.id}</p>
          </div>
          <div>
            {request.status === 'success' ? (
              <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-semibold bg-green-100 text-green-800">
                <CheckCircle className="h-4 w-4 mr-1" />
                Success
              </span>
            ) : (
              <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-semibold bg-red-100 text-red-800">
                <XCircle className="h-4 w-4 mr-1" />
                Error
              </span>
            )}
          </div>
        </div>

        {/* Metadata Grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 pt-4 border-t border-gray-200">
          <div>
            <p className="text-xs text-gray-500 mb-1">Model</p>
            <p className="text-sm font-semibold text-gray-900">{request.model}</p>
          </div>
          <div>
            <p className="text-xs text-gray-500 mb-1">Provider</p>
            <p className="text-sm font-semibold text-gray-900 capitalize">{request.provider}</p>
          </div>
          <div>
            <p className="text-xs text-gray-500 mb-1">Created</p>
            <p className="text-sm font-semibold text-gray-900">
              {new Date(request.created_at).toLocaleString()}
            </p>
          </div>
          <div>
            <p className="text-xs text-gray-500 mb-1">Completed</p>
            <p className="text-sm font-semibold text-gray-900">
              {request.completed_at ? new Date(request.completed_at).toLocaleString() : 'N/A'}
            </p>
          </div>
        </div>
      </div>

      {/* Metrics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
        {/* Cost */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center mb-3">
            <div className="p-2 bg-green-100 rounded-lg">
              <DollarSign className="h-5 w-5 text-green-600" />
            </div>
            <h3 className="ml-3 text-lg font-semibold text-gray-900">Cost</h3>
          </div>
          <div className="space-y-2">
            <div className="flex justify-between">
              <span className="text-sm text-gray-600">Input:</span>
              <span className="text-sm font-medium text-gray-900">
                ${request.input_cost_usd?.toFixed(8) || '0.00000000'}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-gray-600">Output:</span>
              <span className="text-sm font-medium text-gray-900">
                ${request.output_cost_usd?.toFixed(8) || '0.00000000'}
              </span>
            </div>
            <div className="flex justify-between pt-2 border-t border-gray-200">
              <span className="text-sm font-semibold text-gray-900">Total:</span>
              <span className="text-sm font-bold text-gray-900">
                ${request.total_cost_usd?.toFixed(6) || '0.000000'}
              </span>
            </div>
          </div>
        </div>

        {/* Tokens */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center mb-3">
            <div className="p-2 bg-blue-100 rounded-lg">
              <Zap className="h-5 w-5 text-blue-600" />
            </div>
            <h3 className="ml-3 text-lg font-semibold text-gray-900">Tokens</h3>
          </div>
          <div className="space-y-2">
            <div className="flex justify-between">
              <span className="text-sm text-gray-600">Input:</span>
              <span className="text-sm font-medium text-gray-900">
                {request.input_tokens?.toLocaleString() || 'N/A'}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-gray-600">Output:</span>
              <span className="text-sm font-medium text-gray-900">
                {request.output_tokens?.toLocaleString() || 'N/A'}
              </span>
            </div>
            <div className="flex justify-between pt-2 border-t border-gray-200">
              <span className="text-sm font-semibold text-gray-900">Total:</span>
              <span className="text-sm font-bold text-gray-900">
                {request.total_tokens?.toLocaleString() || 'N/A'}
              </span>
            </div>
          </div>
        </div>

        {/* Performance */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center mb-3">
            <div className="p-2 bg-purple-100 rounded-lg">
              <Clock className="h-5 w-5 text-purple-600" />
            </div>
            <h3 className="ml-3 text-lg font-semibold text-gray-900">Performance</h3>
          </div>
          <div className="space-y-2">
            <div className="flex justify-between">
              <span className="text-sm text-gray-600">Latency:</span>
              <span className="text-sm font-medium text-gray-900">
                {request.latency_ms ? `${request.latency_ms}ms` : 'N/A'}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-gray-600">Tokens/sec:</span>
              <span className="text-sm font-medium text-gray-900">
                {request.latency_ms && request.output_tokens
                  ? ((request.output_tokens / request.latency_ms) * 1000).toFixed(1)
                  : 'N/A'}
              </span>
            </div>
            <div className="flex justify-between pt-2 border-t border-gray-200">
              <span className="text-sm font-semibold text-gray-900">Cost/1K tokens:</span>
              <span className="text-sm font-bold text-gray-900">
                {request.total_cost_usd && request.total_tokens
                  ? `$${((request.total_cost_usd / request.total_tokens) * 1000).toFixed(4)}`
                  : 'N/A'}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Error Message (if any) */}
      {request.error_message && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
          <h3 className="text-sm font-semibold text-red-800 mb-2">Error Message</h3>
          <p className="text-sm text-red-700">{request.error_message}</p>
        </div>
      )}

      {/* Prompt */}
      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-3">Prompt</h3>
        <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
          <pre className="text-sm text-gray-800 whitespace-pre-wrap font-mono">
            {request.prompt_text}
          </pre>
        </div>
      </div>

      {/* Response */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-3">Response</h3>
        {request.response_text ? (
          <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
            <pre className="text-sm text-gray-800 whitespace-pre-wrap font-mono">
              {request.response_text}
            </pre>
          </div>
        ) : (
          <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
            <p className="text-sm text-gray-500 italic">No response (request failed)</p>
          </div>
        )}
      </div>
    </div>
  );
}