param (
    [string]$Command = "install",
    [string]$Path = ""
)

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

if ($Path -ne "") {
    python "$ScriptDir\install.py" $Command "$Path"
} else {
    python "$ScriptDir\install.py" $Command
}
