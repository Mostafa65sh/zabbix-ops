import { ServersPage } from './routes';
import type { FrontendModuleDefinition } from '../../../frontend/src/modules/types';

export const serversModule: FrontendModuleDefinition = {
  id: 'servers',
  name: 'Servers',
  version: '1.0.0',
  description: 'Server inventory, host groups, OS, hardware, and lifecycle management',
  enabled: true,
  route: '/servers',
  navItem: {
    label: 'Servers',
    path: '/servers',
    order: 2,
  },
  permissions: ['module.servers.view'],
  component: ServersPage,
};

export default serversModule;
