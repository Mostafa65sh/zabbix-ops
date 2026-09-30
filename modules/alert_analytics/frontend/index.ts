import { AlertAnalyticsPage } from './routes';

export const alert_analyticsModule = {
  id: 'alert_analytics',
  name: 'Alert Analytics',
  version: '0.1.0',
  description: 'MTTR, MTBF, alert volume distribution, and noisy trigger analysis',
  enabled: true,
  route: '/alert_analytics',
  navItem: {
    label: 'Alert Analytics',
    path: '/alert_analytics',
    order: 19
  },
  permissions: ['module.alert_analytics.view'],
  component: AlertAnalyticsPage
};
