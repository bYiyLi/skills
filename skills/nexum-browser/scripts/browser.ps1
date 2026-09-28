$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$browser = Join-Path $scriptDir "browser"
$browserArgs = @($args)
$argvSentinel = "__NEXUM_BROWSER_WINDOWS_ARGV__"
$argvRootEnvName = "NEXUM_BROWSER_ARGV_ROOT"
$argvJson = if ($browserArgs.Count -eq 0) {
    "[]"
} else {
    ConvertTo-Json -Compress -InputObject @($browserArgs)
}

function Test-PythonExecutable {
    param(
        [Parameter(Mandatory = $true)]
        [string] $Executable,
        [string[]] $PrefixArgs = @()
    )

    try {
        & $Executable @PrefixArgs -c "import sys; print(sys.executable)" *> $null
        return $LASTEXITCODE -eq 0
    } catch {
        return $false
    }
}

function Resolve-PythonCommand {
    if ($env:NEXUM_BROWSER_PYTHON) {
        $override = Get-Command (
            $env:NEXUM_BROWSER_PYTHON
        ) -ErrorAction SilentlyContinue
        if ($override -and (Test-PythonExecutable $override.Source)) {
            return [PSCustomObject]@{
                Executable = $override.Source
                PrefixArgs = @()
            }
        }
        throw "NEXUM_BROWSER_PYTHON is not a usable Python interpreter"
    }

    $uv = Get-Command "uv.exe" -ErrorAction SilentlyContinue
    if ($uv) {
        $uvPython = $null
        try {
            $uvPython = (
                & $uv.Source python find 2>$null | Select-Object -First 1
            )
        } catch {
            $uvPython = $null
        }
        if ($uvPython) {
            $uvPython = $uvPython.Trim()
        }
        if (
            $uvPython -and
            (Test-Path -LiteralPath $uvPython) -and
            (Test-PythonExecutable $uvPython)
        ) {
            return [PSCustomObject]@{
                Executable = $uvPython
                PrefixArgs = @()
            }
        }
    }

    $py = Get-Command "py.exe" -ErrorAction SilentlyContinue
    if ($py -and (Test-PythonExecutable $py.Source @("-3"))) {
        return [PSCustomObject]@{
            Executable = $py.Source
            PrefixArgs = @("-3")
        }
    }

    $python = Get-Command "python.exe" -ErrorAction SilentlyContinue
    if ($python -and (Test-PythonExecutable $python.Source)) {
        return [PSCustomObject]@{
            Executable = $python.Source
            PrefixArgs = @()
        }
    }

    return $null
}

$pythonCommand = Resolve-PythonCommand
if ($null -eq $pythonCommand) {
    throw "No usable Python interpreter was found for nexum-browser"
}

$prefixArgs = @($pythonCommand.PrefixArgs)
$argvTempRoot = [IO.Path]::GetTempPath()
$argvFile = Join-Path $argvTempRoot (
    "nexum-browser-argv-" +
    [Guid]::NewGuid().ToString("N") +
    ".json"
)
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
$browserExitCode = 1
try {
    [Environment]::SetEnvironmentVariable(
        $argvRootEnvName,
        $argvTempRoot,
        "Process"
    )
    [IO.File]::WriteAllText($argvFile, $argvJson, $utf8NoBom)
    & $pythonCommand.Executable @prefixArgs $browser $argvSentinel $argvFile
    $browserExitCode = $LASTEXITCODE
} finally {
    [Environment]::SetEnvironmentVariable(
        $argvRootEnvName,
        $null,
        "Process"
    )
    Remove-Item -LiteralPath $argvFile -Force -ErrorAction SilentlyContinue
}
exit $browserExitCode
