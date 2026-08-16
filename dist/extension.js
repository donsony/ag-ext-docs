"use strict";
var __create = Object.create;
var __defProp = Object.defineProperty;
var __getOwnPropDesc = Object.getOwnPropertyDescriptor;
var __getOwnPropNames = Object.getOwnPropertyNames;
var __getProtoOf = Object.getPrototypeOf;
var __hasOwnProp = Object.prototype.hasOwnProperty;
var __export = (target, all) => {
  for (var name in all)
    __defProp(target, name, { get: all[name], enumerable: true });
};
var __copyProps = (to, from, except, desc) => {
  if (from && typeof from === "object" || typeof from === "function") {
    for (let key of __getOwnPropNames(from))
      if (!__hasOwnProp.call(to, key) && key !== except)
        __defProp(to, key, { get: () => from[key], enumerable: !(desc = __getOwnPropDesc(from, key)) || desc.enumerable });
  }
  return to;
};
var __toESM = (mod, isNodeMode, target) => (target = mod != null ? __create(__getProtoOf(mod)) : {}, __copyProps(
  // If the importer is in node compatibility mode or this is not an ESM
  // file that has been converted to a CommonJS file using a Babel-
  // compatible transform (i.e. "__esModule" has not been set), then set
  // "default" to the CommonJS "module.exports" for node compatibility.
  isNodeMode || !mod || !mod.__esModule ? __defProp(target, "default", { value: mod, enumerable: true }) : target,
  mod
));
var __toCommonJS = (mod) => __copyProps(__defProp({}, "__esModule", { value: true }), mod);

// src/extension.ts
var extension_exports = {};
__export(extension_exports, {
  activate: () => activate,
  deactivate: () => deactivate
});
module.exports = __toCommonJS(extension_exports);
var vscode3 = __toESM(require("vscode"));
var path4 = __toESM(require("path"));
var fs4 = __toESM(require("fs"));

// src/syncRunner.ts
var vscode = __toESM(require("vscode"));
var import_child_process = require("child_process");
var path = __toESM(require("path"));
var fs = __toESM(require("fs"));
var SyncRunner = class {
  outputChannel;
  extensionPath;
  constructor(context, outputChannel) {
    this.extensionPath = context.extensionPath;
    this.outputChannel = outputChannel;
  }
  getPythonPath() {
    const config = vscode.workspace.getConfiguration("agDocsSync");
    const customPath = config.get("pythonPath");
    if (customPath && customPath.trim().length > 0) {
      return customPath.trim();
    }
    return process.platform === "win32" ? "python" : "python3";
  }
  async runSync(workspacePath, conversationId) {
    const targetWorkspace = workspacePath || this.getActiveWorkspacePath();
    if (!targetWorkspace) {
      return { success: false, message: "No active workspace folder found." };
    }
    const scriptPath = path.join(this.extensionPath, "scripts", "sync_docs.py");
    if (!fs.existsSync(scriptPath)) {
      return { success: false, message: `Sync script not found at: ${scriptPath}` };
    }
    const args = [scriptPath, "--workspace", targetWorkspace];
    if (conversationId) {
      args.push("--conversation-id", conversationId);
    }
    this.outputChannel.appendLine(`
[${(/* @__PURE__ */ new Date()).toLocaleTimeString()}] Running Antigravity Docs Sync for: ${targetWorkspace}`);
    return new Promise((resolve2) => {
      const pythonExe = this.getPythonPath();
      const child = (0, import_child_process.spawn)(pythonExe, args, {
        cwd: targetWorkspace,
        env: { ...process.env, PYTHONIOENCODING: "utf-8" }
      });
      let stdout = "";
      let stderr = "";
      child.stdout.on("data", (data) => {
        const text = data.toString();
        stdout += text;
        this.outputChannel.append(text);
      });
      child.stderr.on("data", (data) => {
        const text = data.toString();
        stderr += text;
        this.outputChannel.append(text);
      });
      child.on("close", (code) => {
        if (code === 0) {
          this.outputChannel.appendLine(`[${(/* @__PURE__ */ new Date()).toLocaleTimeString()}] \u2705 Sync completed successfully.`);
          resolve2({ success: true, message: stdout.trim() || "Sync completed successfully." });
        } else {
          this.outputChannel.appendLine(`[${(/* @__PURE__ */ new Date()).toLocaleTimeString()}] \u274C Sync failed with exit code ${code}.`);
          resolve2({ success: false, message: stderr.trim() || `Sync failed with exit code ${code}.` });
        }
      });
      child.on("error", (err) => {
        this.outputChannel.appendLine(`[${(/* @__PURE__ */ new Date()).toLocaleTimeString()}] \u274C Failed to start Python process: ${err.message}`);
        resolve2({ success: false, message: `Could not launch Python (${pythonExe}): ${err.message}` });
      });
    });
  }
  async runInstallCommand(command, extraArgs = []) {
    const installScript = path.join(this.extensionPath, "install.py");
    const pythonExe = this.getPythonPath();
    const args = [installScript, command, ...extraArgs];
    this.outputChannel.appendLine(`
[${(/* @__PURE__ */ new Date()).toLocaleTimeString()}] Running: python install.py ${command} ${extraArgs.join(" ")}`);
    return new Promise((resolve2) => {
      const child = (0, import_child_process.spawn)(pythonExe, args, {
        cwd: this.extensionPath,
        env: { ...process.env, PYTHONIOENCODING: "utf-8" }
      });
      let stdout = "";
      let stderr = "";
      child.stdout.on("data", (data) => {
        const text = data.toString();
        stdout += text;
        this.outputChannel.append(text);
      });
      child.stderr.on("data", (data) => {
        const text = data.toString();
        stderr += text;
        this.outputChannel.append(text);
      });
      child.on("close", (code) => {
        if (code === 0) {
          resolve2({ success: true, message: stdout });
        } else {
          resolve2({ success: false, message: stderr || stdout });
        }
      });
      child.on("error", (err) => {
        resolve2({ success: false, message: `Failed to run command: ${err.message}` });
      });
    });
  }
  getActiveWorkspacePath() {
    if (vscode.workspace.workspaceFolders && vscode.workspace.workspaceFolders.length > 0) {
      return vscode.workspace.workspaceFolders[0].uri.fsPath;
    }
    return void 0;
  }
};

// src/configManager.ts
var os = __toESM(require("os"));
var path2 = __toESM(require("path"));
var fs2 = __toESM(require("fs"));
var ConfigManager = class {
  static PLUGIN_NAME = "ag-docs-sync";
  static getGlobalPluginDir() {
    return path2.join(os.homedir(), ".gemini", "config", "plugins", this.PLUGIN_NAME);
  }
  static getGlobalConfigFile() {
    return path2.join(this.getGlobalPluginDir(), "config.json");
  }
  static ensureAgentPluginLinked(extensionPath, outputChannel) {
    try {
      const destDir = this.getGlobalPluginDir();
      if (!fs2.existsSync(destDir)) {
        fs2.mkdirSync(destDir, { recursive: true });
      }
      const itemsToSync = ["plugin.json", "hooks.json", "config.default.json", "scripts", "rules", "skills", "README.md"];
      for (const item of itemsToSync) {
        const srcPath = path2.join(extensionPath, item);
        const dstPath = path2.join(destDir, item);
        if (!fs2.existsSync(srcPath)) {
          continue;
        }
        const stat = fs2.statSync(srcPath);
        if (stat.isDirectory()) {
          this.copyFolderRecursive(srcPath, dstPath);
        } else {
          fs2.copyFileSync(srcPath, dstPath);
        }
      }
      const configFile = this.getGlobalConfigFile();
      if (!fs2.existsSync(configFile)) {
        const defaultConfig = path2.join(extensionPath, "config.default.json");
        if (fs2.existsSync(defaultConfig)) {
          fs2.copyFileSync(defaultConfig, configFile);
        }
      }
      outputChannel.appendLine(`[Agent Sync] Verified AI Agent plugin registration at: ${destDir}`);
    } catch (err) {
      outputChannel.appendLine(`[Agent Sync Warning] Could not auto-link agent plugin: ${err.message}`);
    }
  }
  static getGlobalConfig() {
    const cfgFile = this.getGlobalConfigFile();
    if (fs2.existsSync(cfgFile)) {
      try {
        const raw = fs2.readFileSync(cfgFile, "utf-8");
        return JSON.parse(raw);
      } catch {
      }
    }
    return { enabled: true, exclude_projects: [] };
  }
  static saveGlobalConfig(config) {
    const cfgFile = this.getGlobalConfigFile();
    const destDir = this.getGlobalPluginDir();
    if (!fs2.existsSync(destDir)) {
      fs2.mkdirSync(destDir, { recursive: true });
    }
    fs2.writeFileSync(cfgFile, JSON.stringify(config, null, 2), "utf-8");
  }
  static isWorkspaceExcluded(workspacePath) {
    const config = this.getGlobalConfig();
    const exclusions = config.exclude_projects || [];
    const normalized = path2.resolve(workspacePath).toLowerCase();
    return exclusions.some((p) => path2.resolve(p).toLowerCase() === normalized);
  }
  static copyFolderRecursive(source, target) {
    if (!fs2.existsSync(target)) {
      fs2.mkdirSync(target, { recursive: true });
    }
    const files = fs2.readdirSync(source);
    for (const file of files) {
      if (file === "__pycache__" || file.endsWith(".pyc")) {
        continue;
      }
      const curSource = path2.join(source, file);
      const curTarget = path2.join(target, file);
      if (fs2.lstatSync(curSource).isDirectory()) {
        this.copyFolderRecursive(curSource, curTarget);
      } else {
        fs2.copyFileSync(curSource, curTarget);
      }
    }
  }
};

// src/treeProvider.ts
var vscode2 = __toESM(require("vscode"));
var path3 = __toESM(require("path"));
var fs3 = __toESM(require("fs"));
var DocItem = class extends vscode2.TreeItem {
  constructor(label, collapsibleState, fsPath, isDirectory, category) {
    super(label, collapsibleState);
    this.label = label;
    this.collapsibleState = collapsibleState;
    this.fsPath = fsPath;
    this.isDirectory = isDirectory;
    this.category = category;
    this.tooltip = this.fsPath;
    this.description = category || "";
    if (!isDirectory) {
      this.command = {
        command: "vscode.open",
        title: "Open Document",
        arguments: [vscode2.Uri.file(this.fsPath)]
      };
      this.contextValue = "docFile";
      if (this.label.endsWith(".md")) {
        this.iconPath = new vscode2.ThemeIcon("markdown");
      } else if (this.label.endsWith(".json") || this.label.endsWith(".jsonl")) {
        this.iconPath = new vscode2.ThemeIcon("json");
      } else {
        this.iconPath = new vscode2.ThemeIcon("file");
      }
    } else {
      this.contextValue = "docFolder";
      if (this.label === "session-logs") {
        this.iconPath = new vscode2.ThemeIcon("history");
      } else if (this.label === "plans") {
        this.iconPath = new vscode2.ThemeIcon("list-ordered");
      } else if (this.label === "decisions") {
        this.iconPath = new vscode2.ThemeIcon("lightbulb");
      } else if (this.label === "walkthroughs") {
        this.iconPath = new vscode2.ThemeIcon("check-all");
      } else {
        this.iconPath = new vscode2.ThemeIcon("folder");
      }
    }
  }
};
var DocsTreeDataProvider = class {
  constructor(workspaceRoot) {
    this.workspaceRoot = workspaceRoot;
  }
  _onDidChangeTreeData = new vscode2.EventEmitter();
  onDidChangeTreeData = this._onDidChangeTreeData.event;
  refresh(workspaceRoot) {
    if (workspaceRoot) {
      this.workspaceRoot = workspaceRoot;
    }
    this._onDidChangeTreeData.fire();
  }
  getTreeItem(element) {
    return element;
  }
  getChildren(element) {
    if (!this.workspaceRoot) {
      return Promise.resolve([]);
    }
    const docsDir = path3.join(this.workspaceRoot, ".docs");
    if (!fs3.existsSync(docsDir)) {
      return Promise.resolve([]);
    }
    if (!element) {
      return Promise.resolve(this.getItemsInDirectory(docsDir));
    } else if (element.isDirectory) {
      return Promise.resolve(this.getItemsInDirectory(element.fsPath));
    }
    return Promise.resolve([]);
  }
  getItemsInDirectory(dirPath) {
    if (!fs3.existsSync(dirPath)) {
      return [];
    }
    const items = [];
    try {
      const entries = fs3.readdirSync(dirPath, { withFileTypes: true });
      entries.sort((a, b) => {
        if (a.isDirectory() && !b.isDirectory()) return -1;
        if (!a.isDirectory() && b.isDirectory()) return 1;
        return a.name.localeCompare(b.name);
      });
      for (const entry of entries) {
        if (entry.name.startsWith(".")) continue;
        const fullPath = path3.join(dirPath, entry.name);
        const isDir = entry.isDirectory();
        items.push(
          new DocItem(
            entry.name,
            isDir ? vscode2.TreeItemCollapsibleState.Collapsed : vscode2.TreeItemCollapsibleState.None,
            fullPath,
            isDir
          )
        );
      }
    } catch {
    }
    return items;
  }
};

// src/extension.ts
var statusBarItem;
function activate(context) {
  const outputChannel = vscode3.window.createOutputChannel("Antigravity Docs Sync");
  outputChannel.appendLine("\u{1F680} Antigravity Docs Sync Extension activated.");
  const syncRunner = new SyncRunner(context, outputChannel);
  ConfigManager.ensureAgentPluginLinked(context.extensionPath, outputChannel);
  const initialWorkspace = syncRunner.getActiveWorkspacePath();
  const treeDataProvider = new DocsTreeDataProvider(initialWorkspace);
  vscode3.window.registerTreeDataProvider("agDocsTreeView", treeDataProvider);
  statusBarItem = vscode3.window.createStatusBarItem(vscode3.StatusBarAlignment.Right, 100);
  statusBarItem.command = "agDocsSync.syncNow";
  context.subscriptions.push(statusBarItem);
  updateStatusBar(initialWorkspace);
  const syncNowCommand = vscode3.commands.registerCommand("agDocsSync.syncNow", async () => {
    const ws = syncRunner.getActiveWorkspacePath();
    if (!ws) {
      vscode3.window.showWarningMessage("Antigravity Docs: Please open a workspace folder first.");
      return;
    }
    if (ConfigManager.isWorkspaceExcluded(ws)) {
      const choice = await vscode3.window.showWarningMessage(
        "This workspace is currently excluded from Antigravity Docs sync. Re-enable it?",
        "Re-enable and Sync",
        "Cancel"
      );
      if (choice === "Re-enable and Sync") {
        await vscode3.commands.executeCommand("agDocsSync.includeWorkspace");
      } else {
        return;
      }
    }
    await vscode3.window.withProgress(
      {
        location: vscode3.ProgressLocation.Notification,
        title: "Antigravity Docs: Syncing project artifacts and session logs...",
        cancellable: false
      },
      async () => {
        statusBarItem.text = "$(sync~spin) Docs: Syncing...";
        const result = await syncRunner.runSync(ws);
        if (result.success) {
          vscode3.window.showInformationMessage("\u2705 Antigravity Docs: Documentation synced successfully!");
          treeDataProvider.refresh(ws);
        } else {
          vscode3.window.showErrorMessage(`\u274C Antigravity Docs Sync failed: ${result.message}`);
        }
        updateStatusBar(ws);
      }
    );
  });
  const openDocsCommand = vscode3.commands.registerCommand("agDocsSync.openDocs", async () => {
    const ws = syncRunner.getActiveWorkspacePath();
    if (!ws) return;
    const docsDir = path4.join(ws, ".docs");
    if (!fs4.existsSync(docsDir)) {
      vscode3.window.showInformationMessage('No .docs/ folder found. Run "Antigravity Docs: Sync Now" to generate it.');
      return;
    }
    const indexFile = path4.join(docsDir, "index.md");
    if (fs4.existsSync(indexFile)) {
      const doc = await vscode3.workspace.openTextDocument(vscode3.Uri.file(indexFile));
      await vscode3.window.showTextDocument(doc);
    } else {
      await vscode3.commands.executeCommand("revealFileInOS", vscode3.Uri.file(docsDir));
    }
  });
  const openSessionLogsCommand = vscode3.commands.registerCommand("agDocsSync.openSessionLogs", async () => {
    const ws = syncRunner.getActiveWorkspacePath();
    if (!ws) return;
    const logsDir = path4.join(ws, ".docs", "session-logs");
    if (!fs4.existsSync(logsDir)) {
      vscode3.window.showInformationMessage("No session logs archived in .docs/session-logs yet.");
      return;
    }
    await vscode3.commands.executeCommand("revealFileInOS", vscode3.Uri.file(logsDir));
  });
  const toggleSyncCommand = vscode3.commands.registerCommand("agDocsSync.toggleSync", async () => {
    const cfg = ConfigManager.getGlobalConfig();
    const current = cfg.enabled !== false;
    cfg.enabled = !current;
    ConfigManager.saveGlobalConfig(cfg);
    const statusText = cfg.enabled ? "\u{1F7E2} Enabled" : "\u{1F534} Disabled";
    vscode3.window.showInformationMessage(`Antigravity Docs: Auto-sync is now ${statusText} globally.`);
    updateStatusBar(syncRunner.getActiveWorkspacePath());
  });
  const excludeWorkspaceCommand = vscode3.commands.registerCommand("agDocsSync.excludeWorkspace", async () => {
    const ws = syncRunner.getActiveWorkspacePath();
    if (!ws) return;
    const res = await syncRunner.runInstallCommand("exclude", [ws]);
    vscode3.window.showInformationMessage(`Antigravity Docs: Excluded workspace "${path4.basename(ws)}".`);
    updateStatusBar(ws);
  });
  const includeWorkspaceCommand = vscode3.commands.registerCommand("agDocsSync.includeWorkspace", async () => {
    const ws = syncRunner.getActiveWorkspacePath();
    if (!ws) return;
    const res = await syncRunner.runInstallCommand("unexclude", [ws]);
    vscode3.window.showInformationMessage(`Antigravity Docs: Re-enabled workspace "${path4.basename(ws)}".`);
    updateStatusBar(ws);
  });
  const showStatusCommand = vscode3.commands.registerCommand("agDocsSync.showStatus", async () => {
    outputChannel.show(true);
    await syncRunner.runInstallCommand("status");
  });
  const refreshTreeCommand = vscode3.commands.registerCommand("agDocsSync.refreshTree", () => {
    const ws = syncRunner.getActiveWorkspacePath();
    treeDataProvider.refresh(ws);
  });
  vscode3.workspace.onDidChangeWorkspaceFolders(() => {
    const ws = syncRunner.getActiveWorkspacePath();
    treeDataProvider.refresh(ws);
    updateStatusBar(ws);
  });
  const docsWatcher = vscode3.workspace.createFileSystemWatcher("**/.docs/**");
  docsWatcher.onDidCreate(() => treeDataProvider.refresh());
  docsWatcher.onDidChange(() => treeDataProvider.refresh());
  docsWatcher.onDidDelete(() => treeDataProvider.refresh());
  context.subscriptions.push(docsWatcher);
  context.subscriptions.push(
    syncNowCommand,
    openDocsCommand,
    openSessionLogsCommand,
    toggleSyncCommand,
    excludeWorkspaceCommand,
    includeWorkspaceCommand,
    showStatusCommand,
    refreshTreeCommand
  );
}
function updateStatusBar(workspacePath) {
  const config = vscode3.workspace.getConfiguration("agDocsSync");
  const showItem = config.get("showStatusBarItem", true);
  if (!showItem || !statusBarItem) {
    if (statusBarItem) statusBarItem.hide();
    return;
  }
  const globalCfg = ConfigManager.getGlobalConfig();
  if (globalCfg.enabled === false) {
    statusBarItem.text = "$(circle-slash) Docs: Disabled";
    statusBarItem.tooltip = "Antigravity Docs Sync is disabled globally. Click to sync now.";
    statusBarItem.show();
    return;
  }
  if (workspacePath && ConfigManager.isWorkspaceExcluded(workspacePath)) {
    statusBarItem.text = "$(circle-slash) Docs: Excluded";
    statusBarItem.tooltip = "This workspace is excluded from Antigravity Docs sync. Click to sync now.";
    statusBarItem.show();
    return;
  }
  statusBarItem.text = "$(book) Docs: Active";
  statusBarItem.tooltip = "Antigravity Docs Sync is active. Click to trigger manual sync.";
  statusBarItem.show();
}
function deactivate() {
  if (statusBarItem) {
    statusBarItem.dispose();
  }
}
// Annotate the CommonJS export names for ESM import in node:
0 && (module.exports = {
  activate,
  deactivate
});
//# sourceMappingURL=extension.js.map
