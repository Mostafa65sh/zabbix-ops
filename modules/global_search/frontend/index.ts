import React from 'react';
import { GlobalSearchPage } from './routes';

export const global_searchModule = {
  id: 'global_search',
  name: 'Global Search',
  version: '0.1.0',
  description: 'Cross-platform unified search across hosts, items, problems, and services',
  enabled: true,
  route: '/global_search',
  navItem: {
    label: 'Global Search',
    path: '/global_search',
    order: 8
  },
  permissions: ['module.global_search.view'],
  component: GlobalSearchPage
};
