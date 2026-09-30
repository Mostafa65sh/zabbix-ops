import { TrendDetectionPage } from './routes';

export const trend_detectionModule = {
  id: 'trend_detection',
  name: 'Trend Detection',
  version: '0.1.0',
  description: 'Sustained degradation, baseline comparison, and anomaly candidate identification',
  enabled: true,
  route: '/trend_detection',
  navItem: {
    label: 'Trend Detection',
    path: '/trend_detection',
    order: 15
  },
  permissions: ['module.trend_detection.view'],
  component: TrendDetectionPage
};
