import * as vscode from 'vscode';
import * as path from 'path';
import * as fs from 'fs';
import { SyncRunner } from './syncRunner';
import { ConfigManager } from './configManager';
import { DocsTreeDataProvider } from './treeProvider';

let statusBarItem: vscode.StatusBarItem;

export function activate(context: vscode.ExtensionContext) {
  const outputChannel = vscode.window.createOutputChannel('Antigravity Docs Sync');
  outputChannel.appendLine('🚀 Antigravity Docs Sync Extension activated.');

  const syncRunner = new SyncRunner(context, outputChannel);

  // 1. Ensure Agent Plugin files are synchronized to ~/.gemini/config/plugins/ag-docs-sync
  ConfigManager.ensureAgentPluginLinked(context.extensionPath, outputChannel);

  // 2. Tree Data Provider setup
  const initialWorkspace = syncRunner.getActiveWorkspacePath();
  const treeDataProvider = new DocsTreeDataProvider(initialWorkspace);
  vscode.window.registerTreeDataProvider('agDocsTreeView', treeDataProvider);

  // 3. Status Bar Item
  statusBarItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, 100);
  statusBarItem.command = 'agDocsSync.syncNow';
  context.subscriptions.push(statusBarItem);
  updateStatusBar(initialWorkspace);

  // 4. Command: Sync Now
  const syncNowCommand = vscode.commands.registerCommand('agDocsSync.syncNow', async () => {
    const ws = syncRunner.getActiveWorkspacePath();
    if (!ws) {
      vscode.window.showWarningMessage('Antigravity Docs: Please open a workspace folder first.');
      return;
    }

    if (ConfigManager.isWorkspaceExcluded(ws)) {
      const choice = await vscode.window.showWarningMessage(
        'This workspace is currently excluded from Antigravity Docs sync. Re-enable it?',
        'Re-enable and Sync',
        'Cancel'
      );
      if (choice === 'Re-enable and Sync') {
        await vscode.commands.executeCommand('agDocsSync.includeWorkspace');
      } else {
        return;
      }
    }

    await vscode.window.withProgress(
      {
        location: vscode.ProgressLocation.Notification,
        title: 'Antigravity Docs: Syncing project artifacts and session logs...',
        cancellable: false,
      },
      async () => {
        statusBarItem.text = '$(sync~spin) Docs: Syncing...';
        const result = await syncRunner.runSync(ws);
        if (result.success) {
          vscode.window.showInformationMessage('✅ Antigravity Docs: Documentation synced successfully!');
          treeDataProvider.refresh(ws);
        } else {
          vscode.window.showErrorMessage(`❌ Antigravity Docs Sync failed: ${result.message}`);
        }
        updateStatusBar(ws);
      }
    );
  });

  // 5. Command: Open .docs folder
  const openDocsCommand = vscode.commands.registerCommand('agDocsSync.openDocs', async () => {
    const ws = syncRunner.getActiveWorkspacePath();
    if (!ws) return;
    const docsDir = path.join(ws, '.docs');
    if (!fs.existsSync(docsDir)) {
      vscode.window.showInformationMessage('No .docs/ folder found. Run "Antigravity Docs: Sync Now" to generate it.');
      return;
    }
    const indexFile = path.join(docsDir, 'index.md');
    if (fs.existsSync(indexFile)) {
      const doc = await vscode.workspace.openTextDocument(vscode.Uri.file(indexFile));
      await vscode.window.showTextDocument(doc);
    } else {
      await vscode.commands.executeCommand('revealFileInOS', vscode.Uri.file(docsDir));
    }
  });

  // 6. Command: Open Session Logs
  const openSessionLogsCommand = vscode.commands.registerCommand('agDocsSync.openSessionLogs', async () => {
    const ws = syncRunner.getActiveWorkspacePath();
    if (!ws) return;
    const logsDir = path.join(ws, '.docs', 'session-logs');
    if (!fs.existsSync(logsDir)) {
      vscode.window.showInformationMessage('No session logs archived in .docs/session-logs yet.');
      return;
    }
    await vscode.commands.executeCommand('revealFileInOS', vscode.Uri.file(logsDir));
  });

  // 7. Command: Toggle Global Sync Master Switch
  const toggleSyncCommand = vscode.commands.registerCommand('agDocsSync.toggleSync', async () => {
    const cfg = ConfigManager.getGlobalConfig();
    const current = cfg.enabled !== false;
    cfg.enabled = !current;
    ConfigManager.saveGlobalConfig(cfg);

    const statusText = cfg.enabled ? '🟢 Enabled' : '🔴 Disabled';
    vscode.window.showInformationMessage(`Antigravity Docs: Auto-sync is now ${statusText} globally.`);
    updateStatusBar(syncRunner.getActiveWorkspacePath());
  });

  // 8. Command: Exclude Workspace
  const excludeWorkspaceCommand = vscode.commands.registerCommand('agDocsSync.excludeWorkspace', async () => {
    const ws = syncRunner.getActiveWorkspacePath();
    if (!ws) return;
    const res = await syncRunner.runInstallCommand('exclude', [ws]);
    vscode.window.showInformationMessage(`Antigravity Docs: Excluded workspace "${path.basename(ws)}".`);
    updateStatusBar(ws);
  });

  // 9. Command: Include Workspace
  const includeWorkspaceCommand = vscode.commands.registerCommand('agDocsSync.includeWorkspace', async () => {
    const ws = syncRunner.getActiveWorkspacePath();
    if (!ws) return;
    const res = await syncRunner.runInstallCommand('unexclude', [ws]);
    vscode.window.showInformationMessage(`Antigravity Docs: Re-enabled workspace "${path.basename(ws)}".`);
    updateStatusBar(ws);
  });

  // 10. Command: Show Status & Diagnostics
  const showStatusCommand = vscode.commands.registerCommand('agDocsSync.showStatus', async () => {
    outputChannel.show(true);
    await syncRunner.runInstallCommand('status');
  });

  // 11. Command: Refresh Tree
  const refreshTreeCommand = vscode.commands.registerCommand('agDocsSync.refreshTree', () => {
    const ws = syncRunner.getActiveWorkspacePath();
    treeDataProvider.refresh(ws);
  });

  // 12. Workspace folder switch watcher
  vscode.workspace.onDidChangeWorkspaceFolders(() => {
    const ws = syncRunner.getActiveWorkspacePath();
    treeDataProvider.refresh(ws);
    updateStatusBar(ws);
  });

  // 13. File Watcher for .docs/ changes to keep tree view updated
  const docsWatcher = vscode.workspace.createFileSystemWatcher('**/.docs/**');
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

function updateStatusBar(workspacePath?: string) {
  const config = vscode.workspace.getConfiguration('agDocsSync');
  const showItem = config.get<boolean>('showStatusBarItem', true);

  if (!showItem || !statusBarItem) {
    if (statusBarItem) statusBarItem.hide();
    return;
  }

  const globalCfg = ConfigManager.getGlobalConfig();
  if (globalCfg.enabled === false) {
    statusBarItem.text = '$(circle-slash) Docs: Disabled';
    statusBarItem.tooltip = 'Antigravity Docs Sync is disabled globally. Click to sync now.';
    statusBarItem.show();
    return;
  }

  if (workspacePath && ConfigManager.isWorkspaceExcluded(workspacePath)) {
    statusBarItem.text = '$(circle-slash) Docs: Excluded';
    statusBarItem.tooltip = 'This workspace is excluded from Antigravity Docs sync. Click to sync now.';
    statusBarItem.show();
    return;
  }

  statusBarItem.text = '$(book) Docs: Active';
  statusBarItem.tooltip = 'Antigravity Docs Sync is active. Click to trigger manual sync.';
  statusBarItem.show();
}

export function deactivate() {
  if (statusBarItem) {
    statusBarItem.dispose();
  }
}
