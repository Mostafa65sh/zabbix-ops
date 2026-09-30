import React from 'react';
import { OverviewPage } from './routes';

export const overviewModule = {
  id: 'overview',
  name: 'Overview',
  version: '0.1.0',
  description: 'Infrastructure operations overview, KPIs, and health status',
  enabled: true,
  route: '/overview',
  navItem: {
    label: 'Overview',
    path: '/overview',
    order: 1
  },
  permissions: ['module.overview.view'],
  component: OverviewPage
};
