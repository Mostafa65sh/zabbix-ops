import { TopNPage } from './routes';

export const top_nModule = {
  id: 'top_n',
  name: 'Top N',
  version: '1.0.0',
  description: 'Ranked resource utilization (CPU, memory, disk, network, latency, downtime)',
  enabled: true,
  route: '/top-n',
  navItem: {
    label: 'Top N',
    path: '/top-n',
    order: 6
  },
  permissions: ['module.top_n.view'],
  component: TopNPage
};
