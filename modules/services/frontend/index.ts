import React from 'react';
import { ServicesPage } from './routes';

export const servicesModule = {
  id: 'services',
  name: 'Services',
  version: '0.1.0',
  description: 'Business and technical service dependency tree and SLA tracking',
  enabled: true,
  route: '/services',
  navItem: {
    label: 'Services',
    path: '/services',
    order: 12
  },
  permissions: ['module.services.view'],
  component: ServicesPage
};
