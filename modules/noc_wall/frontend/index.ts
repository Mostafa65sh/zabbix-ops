import React from 'react';
import { NOCWallPage } from './routes';

export const noc_wallModule = {
  id: 'noc_wall',
  name: 'NOC Wall',
  version: '0.1.0',
  description: 'Fullscreen rotating operations wallboard for 24/7 monitoring centers',
  enabled: true,
  route: '/noc_wall',
  navItem: {
    label: 'NOC Wall',
    path: '/noc_wall',
    order: 20
  },
  permissions: ['module.noc_wall.view'],
  component: NOCWallPage
};
