import { NetworkOperationsPage } from './routes';

export const networkModule = {
  id: 'network',
  name: 'Network Operations',
  version: '0.1.0',
  description: 'Network switch, router, interface, port utilization, and topology observability',
  enabled: true,
  route: '/network',
  navItem: {
    label: 'Network Operations',
    path: '/network',
    order: 9
  },
  permissions: ['module.network.view'],
  component: NetworkOperationsPage
};
