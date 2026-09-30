import type { FrontendModuleDefinition, NavigationItem } from './types';

class ModuleRegistry {
  private modules: Map<string, FrontendModuleDefinition> = new Map();

  /**
   * Register a module in the platform frontend.
   */
  public register(module: FrontendModuleDefinition): void {
    if (this.modules.has(module.id)) {
      console.warn(`[ModuleRegistry] Module '${module.id}' is already registered. Overwriting.`);
    }
    this.modules.set(module.id, module);
  }

  /**
   * Returns all registered modules.
   */
  public getAll(): FrontendModuleDefinition[] {
    return Array.from(this.modules.values());
  }

  /**
   * Returns only enabled modules.
   */
  public getEnabled(): FrontendModuleDefinition[] {
    return this.getAll().filter((m) => m.enabled);
  }

  /**
   * Returns sorted navigation items from enabled modules.
   */
  public getNavigationItems(): NavigationItem[] {
    return this.getEnabled()
      .filter((m): m is FrontendModuleDefinition & { navItem: NavigationItem } => !!m.navItem)
      .map((m) => m.navItem)
      .sort((a, b) => a.order - b.order);
  }

  /**
   * Enable or disable a module in the UI.
   */
  public setEnabled(moduleId: string, enabled: boolean): void {
    const mod = this.modules.get(moduleId);
    if (mod) {
      mod.enabled = enabled;
    }
  }

  /**
   * Retrieve a specific module by ID.
   */
  public getModule(moduleId: string): FrontendModuleDefinition | undefined {
    return this.modules.get(moduleId);
  }
}

export const moduleRegistry = new ModuleRegistry();
