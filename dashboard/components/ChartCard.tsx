/**
 * Cost Melt Dashboard - Chart Card Component
 * 
 * Card wrapper with title and chart inside.
 */

import { ReactNode } from 'react';
import Card, { CardHeader, CardTitle, CardContent } from './Card';

interface ChartCardProps {
  title: string;
  children: ReactNode;
  className?: string;
}

export default function ChartCard({ title, children, className }: ChartCardProps) {
  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
      </CardHeader>
      <CardContent>
        {children}
      </CardContent>
    </Card>
  );
}

