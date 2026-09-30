import { ReportsPage } from './routes';

export const reportsModule = {
  id: 'reports',
  name: 'Reports',
  version: '0.1.0',
  description: 'Scheduled and on-demand PDF/CSV availability, SLA, and capacity reports',
  enabled: true,
  route: '/reports',
  navItem: {
    label: 'Reports',
    path: '/reports',
    order: 18
  },
  permissions: ['module.reports.view'],
  component: ReportsPage
};
