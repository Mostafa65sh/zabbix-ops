import { ProblemsPage } from './routes';

export * from './types';
export * from './api';
export { ProblemsPage } from './routes';

export const problemsModule = {
  id: 'problems',
  name: 'Problems',
  version: '1.0.0',
  description: 'Real-time problem center, active events, suppression, and acknowledge workflows',
  enabled: true,
  route: '/problems',
  navItem: {
    label: 'Problems',
    path: '/problems',
    order: 3,
  },
  permissions: ['module.problems.view'],
  component: ProblemsPage,
};
