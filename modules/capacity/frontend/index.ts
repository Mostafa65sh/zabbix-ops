import { CapacityPlanningPage } from './routes';

export const capacityModule = {
  id: 'capacity',
  name: 'Capacity Planning',
  version: '0.1.0',
  description: 'Resource growth forecasting, threshold tracking, and exhaustion estimation',
  enabled: true,
  route: '/capacity',
  navItem: {
    label: 'Capacity Planning',
    path: '/capacity',
    order: 14
  },
  permissions: ['module.capacity.view'],
  component: CapacityPlanningPage
};
