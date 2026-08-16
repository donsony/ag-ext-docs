import * as vscode from 'vscode';
import * as path from 'path';
import * as fs from 'fs';

export class DocItem extends vscode.TreeItem {
  constructor(
    public readonly label: string,
    public readonly collapsibleState: vscode.TreeItemCollapsibleState,
    public readonly fsPath: string,
    public readonly isDirectory: boolean,
    public readonly category?: string
  ) {
    super(label, collapsibleState);

    this.tooltip = this.fsPath;
    this.description = category || '';

    if (!isDirectory) {
      this.command = {
        command: 'vscode.open',
        title: 'Open Document',
        arguments: [vscode.Uri.file(this.fsPath)]
      };
      this.contextValue = 'docFile';
      if (this.label.endsWith('.md')) {
        this.iconPath = new vscode.ThemeIcon('markdown');
      } else if (this.label.endsWith('.json') || this.label.endsWith('.jsonl')) {
        this.iconPath = new vscode.ThemeIcon('json');
      } else {
        this.iconPath = new vscode.ThemeIcon('file');
      }
    } else {
      this.contextValue = 'docFolder';
      if (this.label === 'session-logs') {
        this.iconPath = new vscode.ThemeIcon('history');
      } else if (this.label === 'plans') {
        this.iconPath = new vscode.ThemeIcon('list-ordered');
      } else if (this.label === 'decisions') {
        this.iconPath = new vscode.ThemeIcon('lightbulb');
      } else if (this.label === 'walkthroughs') {
        this.iconPath = new vscode.ThemeIcon('check-all');
      } else {
        this.iconPath = new vscode.ThemeIcon('folder');
      }
    }
  }
}

export class DocsTreeDataProvider implements vscode.TreeDataProvider<DocItem> {
  private _onDidChangeTreeData: vscode.EventEmitter<DocItem | undefined | void> = new vscode.EventEmitter<DocItem | undefined | void>();
  readonly onDidChangeTreeData: vscode.Event<DocItem | undefined | void> = this._onDidChangeTreeData.event;

  constructor(private workspaceRoot?: string) {}

  public refresh(workspaceRoot?: string): void {
    if (workspaceRoot) {
      this.workspaceRoot = workspaceRoot;
    }
    this._onDidChangeTreeData.fire();
  }

  getTreeItem(element: DocItem): vscode.TreeItem {
    return element;
  }

  getChildren(element?: DocItem): Thenable<DocItem[]> {
    if (!this.workspaceRoot) {
      return Promise.resolve([]);
    }

    const docsDir = path.join(this.workspaceRoot, '.docs');
    if (!fs.existsSync(docsDir)) {
      return Promise.resolve([]);
    }

    if (!element) {
      // Root level of .docs/
      return Promise.resolve(this.getItemsInDirectory(docsDir));
    } else if (element.isDirectory) {
      return Promise.resolve(this.getItemsInDirectory(element.fsPath));
    }

    return Promise.resolve([]);
  }

  private getItemsInDirectory(dirPath: string): DocItem[] {
    if (!fs.existsSync(dirPath)) {
      return [];
    }

    const items: DocItem[] = [];
    try {
      const entries = fs.readdirSync(dirPath, { withFileTypes: true });

      // Sort directories first, then files
      entries.sort((a, b) => {
        if (a.isDirectory() && !b.isDirectory()) return -1;
        if (!a.isDirectory() && b.isDirectory()) return 1;
        return a.name.localeCompare(b.name);
      });

      for (const entry of entries) {
        if (entry.name.startsWith('.')) continue;

        const fullPath = path.join(dirPath, entry.name);
        const isDir = entry.isDirectory();

        items.push(
          new DocItem(
            entry.name,
            isDir ? vscode.TreeItemCollapsibleState.Collapsed : vscode.TreeItemCollapsibleState.None,
            fullPath,
            isDir
          )
        );
      }
    } catch {
      // ignore
    }

    return items;
  }
}
