import { OverviewPage } from './routes';
import type { FrontendModuleDefinition } from '../../../frontend/src/modules/types';

export const overviewModule: FrontendModuleDefinition = {
  id: 'overview',
  name: 'Overview',
  version: '1.0.0',
  description: 'Enterprise operations overview, KPIs, and health status',
  enabled: true,
  route: '/overview',
  navItem: {
    label: 'Overview',
    path: '/overview',
    order: 1,
  },
  permissions: ['module.overview.view'],
  component: OverviewPage,
};

export { OverviewPage };
export * from './types';
