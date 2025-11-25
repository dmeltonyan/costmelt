'use client';

// Dashboard Component - Model Routing Heatmap

interface ModelHeatmapProps {
  data: Array<{
    model: string;
    requests: number;
    percentage: number;
    total_cost: number;
  }>;
}

export default function ModelHeatmap({ data }: ModelHeatmapProps) {
  const maxRequests = Math.max(...data.map(d => d.requests), 1);
  
  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold mb-4">Model Routing Breakdown</h3>
      <div className="space-y-3">
        {data.map((item) => (
          <div key={item.model} className="flex items-center">
            <div className="w-32 text-sm font-medium text-gray-700">
              {item.model}
            </div>
            <div className="flex-1 mx-4">
              <div className="w-full bg-gray-200 rounded-full h-6">
                <div
                  className="bg-blue-600 h-6 rounded-full flex items-center justify-center text-white text-xs font-medium"
                  style={{ width: `${(item.requests / maxRequests) * 100}%` }}
                >
                  {item.requests} ({item.percentage}%)
                </div>
              </div>
            </div>
            <div className="w-24 text-sm text-gray-600 text-right">
              ${item.total_cost.toFixed(4)}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

