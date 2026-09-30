import React from 'react';
import { GraphExplorerPage } from './routes';

export const graph_explorerModule = {
  id: 'graph_explorer',
  name: 'Graph Explorer',
  version: '0.1.0',
  description: 'Interactive multi-series metric visualization and comparison',
  enabled: true,
  route: '/graph_explorer',
  navItem: {
    label: 'Graph Explorer',
    path: '/graph_explorer',
    order: 7
  },
  permissions: ['module.graph_explorer.view'],
  component: GraphExplorerPage
};
