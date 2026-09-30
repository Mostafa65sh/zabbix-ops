import { AvailabilityPage } from './routes';

export const availabilityModule = {
  id: 'availability',
  name: 'Availability',
  version: '0.1.0',
  description: 'Infrastructure and SLA availability reporting and downtime timelines',
  enabled: true,
  route: '/availability',
  navItem: {
    label: 'Availability',
    path: '/availability',
    order: 4
  },
  permissions: ['module.availability.view'],
  component: AvailabilityPage
};
