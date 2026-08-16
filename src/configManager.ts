import * as os from 'os';
import * as path from 'path';
import * as fs from 'fs';
import * as vscode from 'vscode';

export class ConfigManager {
  private static readonly PLUGIN_NAME = 'ag-docs-sync';

  public static getGlobalPluginDir(): string {
    return path.join(os.homedir(), '.gemini', 'config', 'plugins', this.PLUGIN_NAME);
  }

  public static getGlobalConfigFile(): string {
    return path.join(this.getGlobalPluginDir(), 'config.json');
  }

  public static ensureAgentPluginLinked(extensionPath: string, outputChannel: vscode.OutputChannel): void {
    try {
      const destDir = this.getGlobalPluginDir();
      if (!fs.existsSync(destDir)) {
        fs.mkdirSync(destDir, { recursive: true });
      }

      const itemsToSync = ['plugin.json', 'hooks.json', 'config.default.json', 'scripts', 'rules', 'skills', 'README.md'];

      for (const item of itemsToSync) {
        const srcPath = path.join(extensionPath, item);
        const dstPath = path.join(destDir, item);

        if (!fs.existsSync(srcPath)) {
          continue;
        }

        const stat = fs.statSync(srcPath);
        if (stat.isDirectory()) {
          this.copyFolderRecursive(srcPath, dstPath);
        } else {
          fs.copyFileSync(srcPath, dstPath);
        }
      }

      // Initialize config.json if not present
      const configFile = this.getGlobalConfigFile();
      if (!fs.existsSync(configFile)) {
        const defaultConfig = path.join(extensionPath, 'config.default.json');
        if (fs.existsSync(defaultConfig)) {
          fs.copyFileSync(defaultConfig, configFile);
        }
      }

      outputChannel.appendLine(`[Agent Sync] Verified AI Agent plugin registration at: ${destDir}`);
    } catch (err: any) {
      outputChannel.appendLine(`[Agent Sync Warning] Could not auto-link agent plugin: ${err.message}`);
    }
  }

  public static getGlobalConfig(): any {
    const cfgFile = this.getGlobalConfigFile();
    if (fs.existsSync(cfgFile)) {
      try {
        const raw = fs.readFileSync(cfgFile, 'utf-8');
        return JSON.parse(raw);
      } catch {
        // fallback
      }
    }
    return { enabled: true, exclude_projects: [] };
  }

  public static saveGlobalConfig(config: any): void {
    const cfgFile = this.getGlobalConfigFile();
    const destDir = this.getGlobalPluginDir();
    if (!fs.existsSync(destDir)) {
      fs.mkdirSync(destDir, { recursive: true });
    }
    fs.writeFileSync(cfgFile, JSON.stringify(config, null, 2), 'utf-8');
  }

  public static isWorkspaceExcluded(workspacePath: string): boolean {
    const config = this.getGlobalConfig();
    const exclusions: string[] = config.exclude_projects || [];
    const normalized = path.resolve(workspacePath).toLowerCase();
    return exclusions.some(p => path.resolve(p).toLowerCase() === normalized);
  }

  private static copyFolderRecursive(source: string, target: string): void {
    if (!fs.existsSync(target)) {
      fs.mkdirSync(target, { recursive: true });
    }

    const files = fs.readdirSync(source);
    for (const file of files) {
      if (file === '__pycache__' || file.endsWith('.pyc')) {
        continue;
      }
      const curSource = path.join(source, file);
      const curTarget = path.join(target, file);

      if (fs.lstatSync(curSource).isDirectory()) {
        this.copyFolderRecursive(curSource, curTarget);
      } else {
        fs.copyFileSync(curSource, curTarget);
      }
    }
  }
}
