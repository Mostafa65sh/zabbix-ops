import { AvailabilityPage } from './routes';

export * from './types';
export * from './api';
export { AvailabilityPage } from './routes';

export const availabilityModule = {
  id: 'availability',
  name: 'Availability',
  version: '1.0.0',
  description: 'Business service availability, SLA compliance, and outage analysis',
  enabled: true,
  route: '/availability',
  navItem: {
    label: 'Availability',
    path: '/availability',
    order: 4,
  },
  permissions: ['module.availability.view'],
  component: AvailabilityPage,
};
