import { WebMonitoringPage } from './routes';

export const web_monitoringModule = {
  id: 'web_monitoring',
  name: 'Web Monitoring',
  version: '0.1.0',
  description: 'HTTP/S scenario health, response times, SSL/TLS, and URL availability',
  enabled: true,
  route: '/web_monitoring',
  navItem: {
    label: 'Web Monitoring',
    path: '/web_monitoring',
    order: 11
  },
  permissions: ['module.web_monitoring.view'],
  component: WebMonitoringPage
};
