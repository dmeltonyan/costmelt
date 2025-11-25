/**
 * Cost Melt Landing - Section Component
 * 
 * Reusable section wrapper with consistent styling.
 */

import { ReactNode } from 'react';
import { cn } from '../lib/utils';

interface SectionProps {
  children: ReactNode;
  className?: string;
  id?: string;
}

export default function Section({ children, className = '', id }: SectionProps) {
  return (
    <section id={id} className={cn('py-20 md:py-32', className)}>
      <div className="container mx-auto px-6">
        {children}
      </div>
    </section>
  );
}

