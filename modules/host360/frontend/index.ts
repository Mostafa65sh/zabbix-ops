import { Host360Page } from './routes';

export const host360Module = {
  id: 'host360',
  name: 'Host 360',
  version: '1.0.0',
  description: 'Comprehensive 360-degree host telemetry, metrics, and event overlays',
  enabled: true,
  route: '/host360',
  navItem: {
    label: 'Host 360',
    path: '/host360',
    order: 5
  },
  permissions: ['module.host360.view'],
  component: Host360Page
};
