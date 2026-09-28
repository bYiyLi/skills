$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$browser = Join-Path $scriptDir "browser"
$browserArgs = @($args)

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

function Invoke-Browser {
    param(
        [Parameter(Mandatory = $true)]
        [string] $Executable,
        [string[]] $PrefixArgs = @()
    )

    & $Executable @PrefixArgs $browser @browserArgs
    exit $LASTEXITCODE
}

if ($env:NEXUM_BROWSER_PYTHON) {
    $override = Get-Command (
        $env:NEXUM_BROWSER_PYTHON
    ) -ErrorAction SilentlyContinue
    if ($override -and (Test-PythonExecutable $override.Source)) {
        Invoke-Browser $override.Source
    }
    throw "NEXUM_BROWSER_PYTHON is not a usable Python interpreter"
}

$uv = Get-Command "uv.exe" -ErrorAction SilentlyContinue
if ($uv) {
    try {
        $uvPython = (
            & $uv.Source python find 2>$null | Select-Object -First 1
        )
        if (
            $LASTEXITCODE -eq 0 -and
            $uvPython -and
            (Test-Path -LiteralPath $uvPython) -and
            (Test-PythonExecutable $uvPython)
        ) {
            Invoke-Browser $uvPython
        }
    } catch {
    }
}

$py = Get-Command "py.exe" -ErrorAction SilentlyContinue
if ($py -and (Test-PythonExecutable $py.Source @("-3"))) {
    Invoke-Browser $py.Source @("-3")
}

$python = Get-Command "python.exe" -ErrorAction SilentlyContinue
if ($python -and (Test-PythonExecutable $python.Source)) {
    Invoke-Browser $python.Source
}

throw "No usable Python interpreter was found for nexum-browser"
