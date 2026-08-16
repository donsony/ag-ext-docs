param (
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$ScriptArgs
)

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

if ($ScriptArgs.Count -gt 0) {
    python "$ScriptDir\install.py" @ScriptArgs
} else {
    python "$ScriptDir\install.py"
}
