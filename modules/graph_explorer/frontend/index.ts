import { GraphExplorerPage } from './routes';

export const graph_explorerModule = {
  id: 'graph_explorer',
  name: 'Graph Explorer',
  version: '1.0.0',
  description: 'Interactive multi-series metric visualization and comparison',
  enabled: true,
  route: '/graphs',
  navItem: {
    label: 'Graph Explorer',
    path: '/graphs',
    order: 7
  },
  permissions: ['module.graph_explorer.view'],
  component: GraphExplorerPage
};
