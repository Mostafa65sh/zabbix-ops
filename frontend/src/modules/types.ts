import React from 'react';

export interface NavigationItem {
  label: string;
  path: string;
  icon?: string;
  order: number;
}

export interface FrontendModuleDefinition {
  id: string;
  name: string;
  version: string;
  description: string;
  enabled: boolean;
  route?: string;
  navItem?: NavigationItem;
  permissions?: string[];
  component?: React.ComponentType;
}
