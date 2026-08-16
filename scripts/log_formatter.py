#!/usr/bin/env python3
"""
Color-Coded Markdown Session Log Generator for ag-docs-sync
Parses Antigravity transcripts (JSONL) and generates rich, timestamped markdown logs.
"""

import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


class LogFormatter:
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.session_cfg = self.config.get("session_logging", {})
        self.timestamp_fmt = self.config.get("timestamp_format", "%Y-%m-%d_%H%M%S")

    @staticmethod
    def parse_iso_timestamp(ts_str: Optional[str]) -> Optional[datetime]:
        if not ts_str:
            return None
        # Handle '2026-08-16T13:41:07Z' or offsets
        clean_ts = ts_str.replace("Z", "+00:00")
        try:
            return datetime.fromisoformat(clean_ts)
        except Exception:
            return None

    @staticmethod
    def format_timestamp(dt: Optional[datetime], fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
        if not dt:
            return "N/A"
        return dt.strftime(fmt)

    def read_transcript_lines(self, transcript_path: str) -> List[Dict[str, Any]]:
        """Reads JSONL transcript file into a list of parsed objects."""
        path = Path(transcript_path)
        if not path.exists():
            return []

        # If transcript.jsonl was passed, check if transcript_full.jsonl exists in same dir for untruncated content
        full_path = path.parent / "transcript_full.jsonl"
        target_path = full_path if full_path.exists() and full_path.stat().st_size > 0 else path

        entries = []
        try:
            with open(target_path, "r", encoding="utf-8", errors="replace") as f:
                for line_idx, line in enumerate(f):
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        obj = json.loads(line)
                        entries.append(obj)
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            print(f"[ag-docs-sync] Error reading transcript {target_path}: {e}")

        return entries

    def extract_thought_and_content(self, raw_content: str) -> Tuple[Optional[str], str]:
        """Separates <thought>...</thought> blocks from main content."""
        if not raw_content:
            return None, ""

        thoughts = []
        def thought_replacer(match):
            thoughts.append(match.group(1).strip())
            return ""

        clean_content = re.sub(r"<thought>(.*?)</thought>", thought_replacer, raw_content, flags=re.DOTALL)
        clean_content = clean_content.strip()
        thought_text = "\n\n".join(thoughts).strip() if thoughts else None

        return thought_text, clean_content

    def extract_user_request_text(self, raw_text: str) -> str:
        """Extracts clean prompt from <USER_REQUEST> tags if present."""
        if not raw_text:
            return ""
        match = re.search(r"<USER_REQUEST>(.*?)</USER_REQUEST>", raw_text, flags=re.DOTALL)
        if match:
            return match.group(1).strip()
        return raw_text.strip()

    def generate_session_markdown(
        self,
        transcript_path: str,
        conversation_id: str,
        workspace_path: str,
        session_time: Optional[datetime] = None
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Parses the transcript and renders the full color-coded Markdown session log.
        Returns (markdown_content: str, metadata: dict).
        """
        entries = self.read_transcript_lines(transcript_path)
        start_time = None
        end_time = None

        if entries:
            start_time = self.parse_iso_timestamp(entries[0].get("created_at"))
            end_time = self.parse_iso_timestamp(entries[-1].get("created_at"))

        if not session_time:
            session_time = end_time or start_time or datetime.now()

        duration_str = "N/A"
        if start_time and end_time:
            delta = end_time - start_time
            minutes, seconds = divmod(int(delta.total_seconds()), 60)
            hours, minutes = divmod(minutes, 60)
            if hours > 0:
                duration_str = f"{hours}h {minutes}m {seconds}s"
            else:
                duration_str = f"{minutes}m {seconds}s"

        total_steps = len(entries)
        prompt_count = 0
        tool_count = 0
        error_count = 0
        goals: List[str] = []

        md_sections: List[str] = []

        # Header Block
        md_sections.append(f"""# 🚀 Build & Conversation Session Log

> **Session ID:** `{conversation_id}`  
> **Workspace:** `{workspace_path}`  
> **Date & Time:** `{self.format_timestamp(session_time)}`  
> **Duration:** `{duration_str}` | **Total Events:** `{total_steps}`  
""")

        # Process conversation steps
        for idx, entry in enumerate(entries):
            step_idx = entry.get("step_index", idx)
            source = entry.get("source", "")
            step_type = entry.get("type", "")
            status = entry.get("status", "DONE")
            created_at_dt = self.parse_iso_timestamp(entry.get("created_at"))
            ts_display = self.format_timestamp(created_at_dt, "%H:%M:%S")

            raw_content = entry.get("content", "")
            tool_calls = entry.get("tool_calls", [])

            # 1. USER INPUT / INSTRUCTIONS
            if step_type == "USER_INPUT" or source == "USER_EXPLICIT":
                prompt_count += 1
                user_req = self.extract_user_request_text(raw_content)
                if user_req:
                    # Capture first line as goal summary if not already set
                    first_line = user_req.split("\n")[0].strip()
                    if len(first_line) > 120:
                        first_line = first_line[:117] + "..."
                    goals.append(first_line)

                md_sections.append(f"""
---

### 🎯 <span style="color:#0284c7;">Instruction #{prompt_count}</span> <small style="color:#64748b;">(Step {step_idx} • {ts_display})</small>

> [!NOTE]
> **User Request & Goal:**
>
> {self._indent_markdown(user_req or raw_content, 2)}
""")

            # 2. CHECKPOINT / SYSTEM SUMMARIES
            elif step_type == "CHECKPOINT" or (source == "SYSTEM" and "CHECKPOINT" in raw_content):
                md_sections.append(f"""
> [!NOTE]
> 📌 **System Context Checkpoint** *(Context window optimized at {ts_display})*
""")

            # 3. MODEL RESPONSES & REASONING
            elif source == "MODEL" and (step_type == "PLANNER_RESPONSE" or raw_content):
                thought_text, main_text = self.extract_thought_and_content(raw_content)

                # Thought Process Block
                if thought_text and self.session_cfg.get("include_thoughts", True):
                    collapse = self.session_cfg.get("collapse_thoughts", True)
                    open_attr = "" if collapse else " open"
                    md_sections.append(f"""
<details{open_attr}>
<summary>🧠 <b><span style="color:#7c3aed;">Agent Thought Process & Decision Reasoning</span></b> <small style="color:#94a3b8;">({ts_display})</small></summary>

> [!TIP]
> **Internal Reasoning:**
>
> {self._indent_markdown(thought_text, 2)}

</details>
""")

                # Tool Calls
                if tool_calls and self.session_cfg.get("include_tools", True):
                    for tc in tool_calls:
                        tool_count += 1
                        tool_name = tc.get("name", "unknown_tool")
                        args = tc.get("args", {})

                        # Check for ask_question interactive Q&A
                        if tool_name == "ask_question":
                            md_sections.append(self._format_qa_tool(args, ts_display, step_idx))
                        else:
                            md_sections.append(self._format_generic_tool_call(tool_name, args, ts_display, step_idx))

                # Main text response
                if main_text:
                    md_sections.append(f"""
#### 💬 **Assistant Response** <small style="color:#64748b;">({ts_display})</small>

{main_text}
""")

            # 4. TOOL EXECUTION OUTPUT
            elif source == "MODEL" and step_type not in ("PLANNER_RESPONSE", "USER_INPUT"):
                tool_display_name = step_type.replace("_", " ").title()
                is_error = status == "ERROR" or "error" in entry
                if is_error:
                    error_count += 1

                if self.session_cfg.get("include_tools", True):
                    md_sections.append(self._format_tool_output(tool_display_name, raw_content, is_error, ts_display, step_idx))

        # Metadata summary
        meta = {
            "conversation_id": conversation_id,
            "session_time": session_time.strftime("%Y-%m-%d %H:%M:%S"),
            "session_timestamp_tag": session_time.strftime(self.timestamp_fmt),
            "duration": duration_str,
            "total_steps": total_steps,
            "prompt_count": prompt_count,
            "tool_count": tool_count,
            "error_count": error_count,
            "goals": goals,
            "primary_goal": goals[0] if goals else "Antigravity Session Task",
        }

        # Build Summary Card at the top
        summary_card = f"""## 📊 Session Summary & Execution Metrics

| Metric | Value | Metric | Value |
| :--- | :--- | :--- | :--- |
| **Primary Goal** | `{meta['primary_goal']}` | **Session Date** | `{meta['session_time']}` |
| **Total Prompts** | `{prompt_count}` | **Duration** | `{duration_str}` |
| **Tool Executions** | `{tool_count}` | **Issues / Errors** | `{error_count}` |

---
"""
        # Insert summary card right after Header Block
        full_markdown = md_sections[0] + "\n" + summary_card + "\n".join(md_sections[1:])

        # Add Footer
        full_markdown += f"""
---
*Generated automatically by [ag-docs-sync](file:///d:/Development/ag-ext-docs) at {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}*
"""
        return full_markdown, meta

    def _indent_markdown(self, text: str, spaces: int = 2) -> str:
        indent = " " * spaces
        return "\n".join(f"{indent}{line}" if line.strip() else "" for line in text.splitlines())

    def _format_qa_tool(self, args: Dict[str, Any], ts: str, step_idx: int) -> str:
        questions = args.get("questions", [])
        rendered_qs = []
        for q_item in questions:
            q_text = q_item.get("question", "")
            opts = q_item.get("options", [])
            opts_formatted = "\n".join(f"  - [ ] {opt}" for opt in opts)
            rendered_qs.append(f"**Q:** {q_text}\n{opts_formatted}")

        qs_block = "\n\n".join(rendered_qs)
        return f"""
> [!IMPORTANT]
> ❓ **Interactive User Decision / Question Prompt** <small style="color:#d97706;">({ts})</small>
>
> {self._indent_markdown(qs_block, 2)}
"""

    def _format_generic_tool_call(self, tool_name: str, args: Dict[str, Any], ts: str, step_idx: int) -> str:
        summary = args.get("toolSummary") or args.get("toolAction") or tool_name
        if isinstance(summary, str):
            summary = summary.strip('"')

        # Clean display of main arguments
        args_display = {}
        for k, v in args.items():
            if k in ("toolSummary", "toolAction"):
                continue
            if isinstance(v, str) and len(v) > 250:
                args_display[k] = v[:247] + "..."
            else:
                args_display[k] = v

        args_json = json.dumps(args_display, indent=2)

        return f"""
<div style="margin: 8px 0; border-left: 3px solid #10b981; padding-left: 10px;">
  <b>🛠️ Action:</b> <code>{tool_name}</code> — <i>{summary}</i> <small style="color:#64748b;">({ts})</small>
</div>

<details>
<summary>🔍 <b>View Tool Arguments</b></summary>

```json
{args_json}
```
</details>
"""

    def _format_tool_output(self, tool_name: str, output: str, is_error: bool, ts: str, step_idx: int) -> str:
        if not output:
            return ""

        short_preview = output[:300] + ("..." if len(output) > 300 else "")
        if is_error:
            return f"""
> [!CAUTION]
> ❌ **Tool Error ({tool_name})** <small style="color:#dc2626;">({ts})</small>
>
> ```text
> {output}
> ```
"""
        else:
            return f"""
<details>
<summary>📋 <b>Output: {tool_name}</b> <small style="color:#16a34a;">(Completed at {ts})</small></summary>

```text
{output[:3000]}
```
</details>
"""

    def update_timeline_index(self, timeline_path: Path, meta: Dict[str, Any], rel_log_file: str) -> None:
        """Appends or creates the cumulative timeline index in .docs/logs/TIMELINE.md."""
        timeline_path.parent.mkdir(parents=True, exist_ok=True)
        
        new_row = f"| `{meta['session_time']}` | [`{meta['conversation_id'][:8]}...`]({rel_log_file}) | {meta['primary_goal']} | `{meta['duration']}` | `{meta['prompt_count']}` | `{meta['tool_count']}` |"

        if not timeline_path.exists():
            content = f"""# 📜 Antigravity Project Session Timeline

Cumulative historical index of all Antigravity development sessions in this project.

| Timestamp | Session Log | Goal / Objective | Duration | Prompts | Tools |
| :--- | :--- | :--- | :--- | :--- | :--- |
{new_row}
"""
            with open(timeline_path, "w", encoding="utf-8") as f:
                f.write(content)
        else:
            with open(timeline_path, "r", encoding="utf-8") as f:
                existing = f.read()

            # Check if this session row is already recorded
            if meta['conversation_id'] in existing and meta['session_time'] in existing:
                return

            # Append the row
            updated = existing.rstrip() + "\n" + new_row + "\n"
            with open(timeline_path, "w", encoding="utf-8") as f:
                f.write(updated)


if __name__ == "__main__":
    import sys
    formatter = LogFormatter()
    if len(sys.argv) > 1:
        path = sys.argv[1]
        md, metadata = formatter.generate_session_markdown(path, "demo-conv", "/workspace")
        print(md[:1000])
    else:
        print("LogFormatter ready.")
