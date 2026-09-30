import { ApplicationsPage } from './routes';

export const applicationsModule = {
  id: 'applications',
  name: 'Applications',
  version: '0.1.0',
  description: 'Application health, middleware metrics, and service relationships',
  enabled: true,
  route: '/applications',
  navItem: {
    label: 'Applications',
    path: '/applications',
    order: 13
  },
  permissions: ['module.applications.view'],
  component: ApplicationsPage
};
