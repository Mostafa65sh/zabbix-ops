import { AIAndIntelligencePage } from './routes';

export const intelligenceModule = {
  id: 'intelligence',
  name: 'AI & Intelligence',
  version: '0.1.0',
  description: 'Future operational assistant, incident summarization, and root-cause candidate analysis',
  enabled: true,
  route: '/intelligence',
  navItem: {
    label: 'AI & Intelligence',
    path: '/intelligence',
    order: 21
  },
  permissions: ['module.intelligence.view'],
  component: AIAndIntelligencePage
};
