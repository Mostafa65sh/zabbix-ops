import { DatabaseOperationsPage } from './routes';

export const databaseModule = {
  id: 'database',
  name: 'Database Operations',
  version: '0.1.0',
  description: 'Database performance metrics for PostgreSQL, MySQL, Oracle, and SQL Server',
  enabled: true,
  route: '/database',
  navItem: {
    label: 'Database Operations',
    path: '/database',
    order: 10
  },
  permissions: ['module.database.view'],
  component: DatabaseOperationsPage
};
