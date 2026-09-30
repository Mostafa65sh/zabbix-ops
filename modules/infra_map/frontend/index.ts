import { InfrastructureMapPage } from './routes';

export const infra_mapModule = {
  id: 'infra_map',
  name: 'Infrastructure Map',
  version: '0.1.0',
  description: 'Visual topological relationships, dependencies, and incident overlays',
  enabled: true,
  route: '/infra_map',
  navItem: {
    label: 'Infrastructure Map',
    path: '/infra_map',
    order: 16
  },
  permissions: ['module.infra_map.view'],
  component: InfrastructureMapPage
};
