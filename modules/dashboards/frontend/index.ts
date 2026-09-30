import { DashboardBuilderPage } from './routes';

export const dashboardsModule = {
  id: 'dashboards',
  name: 'Dashboard Builder',
  version: '0.1.0',
  description: 'Configurable custom operational dashboards and NOC wall layouts',
  enabled: true,
  route: '/dashboards',
  navItem: {
    label: 'Dashboard Builder',
    path: '/dashboards',
    order: 17
  },
  permissions: ['module.dashboards.view'],
  component: DashboardBuilderPage
};
