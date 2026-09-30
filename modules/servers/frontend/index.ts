import { ServersPage } from './routes';

export const serversModule = {
  id: 'servers',
  name: 'Servers',
  version: '0.1.0',
  description: 'Server inventory, host groups, OS, hardware, and lifecycle management',
  enabled: true,
  route: '/servers',
  navItem: {
    label: 'Servers',
    path: '/servers',
    order: 2
  },
  permissions: ['module.servers.view'],
  component: ServersPage
};
