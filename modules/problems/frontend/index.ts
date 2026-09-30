import React from 'react';
import { ProblemsPage } from './routes';

export const problemsModule = {
  id: 'problems',
  name: 'Problems',
  version: '0.1.0',
  description: 'Real-time problem center, active events, suppression, and acknowledge workflows',
  enabled: true,
  route: '/problems',
  navItem: {
    label: 'Problems',
    path: '/problems',
    order: 3
  },
  permissions: ['module.problems.view'],
  component: ProblemsPage
};
