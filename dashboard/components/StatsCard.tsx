/**
 * Cost Melt Dashboard - Stats Card Component
 * 
 * Metric card for displaying statistics.
 */

import Card, { CardContent } from './Card';
import Metric from './Metric';

interface StatsCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  trend?: {
    value: number;
    isPositive: boolean;
  };
}

export default function StatsCard({ title, value, subtitle, trend }: StatsCardProps) {
  return (
    <Card>
      <CardContent className="p-6">
        <Metric
          label={title}
          value={value}
          subtitle={subtitle}
          trend={trend}
        />
      </CardContent>
    </Card>
  );
}

