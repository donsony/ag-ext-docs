import * as vscode from 'vscode';
import { spawn } from 'child_process';
import * as path from 'path';
import * as fs from 'fs';

export class SyncRunner {
  private outputChannel: vscode.OutputChannel;
  private extensionPath: string;

  constructor(context: vscode.ExtensionContext, outputChannel: vscode.OutputChannel) {
    this.extensionPath = context.extensionPath;
    this.outputChannel = outputChannel;
  }

  private getPythonPath(): string {
    const config = vscode.workspace.getConfiguration('agDocsSync');
    const customPath = config.get<string>('pythonPath');
    if (customPath && customPath.trim().length > 0) {
      return customPath.trim();
    }
    return process.platform === 'win32' ? 'python' : 'python3';
  }

  public async runSync(workspacePath?: string, conversationId?: string): Promise<{ success: boolean; message: string }> {
    const targetWorkspace = workspacePath || this.getActiveWorkspacePath();
    if (!targetWorkspace) {
      return { success: false, message: 'No active workspace folder found.' };
    }

    const scriptPath = path.join(this.extensionPath, 'scripts', 'sync_docs.py');
    if (!fs.existsSync(scriptPath)) {
      return { success: false, message: `Sync script not found at: ${scriptPath}` };
    }

    const args = [scriptPath, '--workspace', targetWorkspace];
    if (conversationId) {
      args.push('--conversation-id', conversationId);
    }

    this.outputChannel.appendLine(`\n[${new Date().toLocaleTimeString()}] Running Antigravity Docs Sync for: ${targetWorkspace}`);
    
    return new Promise((resolve) => {
      const pythonExe = this.getPythonPath();
      const child = spawn(pythonExe, args, {
        cwd: targetWorkspace,
        env: { ...process.env, PYTHONIOENCODING: 'utf-8' },
      });

      let stdout = '';
      let stderr = '';

      child.stdout.on('data', (data) => {
        const text = data.toString();
        stdout += text;
        this.outputChannel.append(text);
      });

      child.stderr.on('data', (data) => {
        const text = data.toString();
        stderr += text;
        this.outputChannel.append(text);
      });

      child.on('close', (code) => {
        if (code === 0) {
          this.outputChannel.appendLine(`[${new Date().toLocaleTimeString()}] ✅ Sync completed successfully.`);
          resolve({ success: true, message: stdout.trim() || 'Sync completed successfully.' });
        } else {
          this.outputChannel.appendLine(`[${new Date().toLocaleTimeString()}] ❌ Sync failed with exit code ${code}.`);
          resolve({ success: false, message: stderr.trim() || `Sync failed with exit code ${code}.` });
        }
      });

      child.on('error', (err) => {
        this.outputChannel.appendLine(`[${new Date().toLocaleTimeString()}] ❌ Failed to start Python process: ${err.message}`);
        resolve({ success: false, message: `Could not launch Python (${pythonExe}): ${err.message}` });
      });
    });
  }

  public async runInstallCommand(command: string, extraArgs: string[] = []): Promise<{ success: boolean; message: string }> {
    const installScript = path.join(this.extensionPath, 'install.py');
    const pythonExe = this.getPythonPath();
    const args = [installScript, command, ...extraArgs];

    this.outputChannel.appendLine(`\n[${new Date().toLocaleTimeString()}] Running: python install.py ${command} ${extraArgs.join(' ')}`);

    return new Promise((resolve) => {
      const child = spawn(pythonExe, args, {
        cwd: this.extensionPath,
        env: { ...process.env, PYTHONIOENCODING: 'utf-8' },
      });

      let stdout = '';
      let stderr = '';

      child.stdout.on('data', (data) => {
        const text = data.toString();
        stdout += text;
        this.outputChannel.append(text);
      });

      child.stderr.on('data', (data) => {
        const text = data.toString();
        stderr += text;
        this.outputChannel.append(text);
      });

      child.on('close', (code) => {
        if (code === 0) {
          resolve({ success: true, message: stdout });
        } else {
          resolve({ success: false, message: stderr || stdout });
        }
      });

      child.on('error', (err) => {
        resolve({ success: false, message: `Failed to run command: ${err.message}` });
      });
    });
  }

  public getActiveWorkspacePath(): string | undefined {
    if (vscode.workspace.workspaceFolders && vscode.workspace.workspaceFolders.length > 0) {
      return vscode.workspace.workspaceFolders[0].uri.fsPath;
    }
    return undefined;
  }
}
