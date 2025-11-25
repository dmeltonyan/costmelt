'use client';

// Dashboard Component - Cost Chart

import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

interface CostChartProps {
  data: Array<{
    date: string;
    cost: number;
    savings: number;
  }>;
}

export default function CostChart({ data }: CostChartProps) {
  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold mb-4">Cost & Savings Over Time</h3>
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="date" />
          <YAxis />
          <Tooltip />
          <Legend />
          <Line type="monotone" dataKey="cost" stroke="#8884d8" name="Cost" />
          <Line type="monotone" dataKey="savings" stroke="#82ca9d" name="Savings" />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

