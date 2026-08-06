$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot

$scripts = @(
    "deck/scripts/deps-windows.ps1",
    "deck/scripts/render-windows.ps1"
)

foreach ($rel in $scripts) {
    $path = Join-Path $RepoRoot $rel
    $tokens = $null
    $errors = $null
    [System.Management.Automation.Language.Parser]::ParseFile($path, [ref]$tokens, [ref]$errors) | Out-Null
    if ($errors.Count -gt 0) {
        $message = ($errors | ForEach-Object { $_.Message }) -join "; "
        throw "PowerShell parse failed for ${rel}: $message"
    }
}

$render = Get-Content (Join-Path $RepoRoot "deck/scripts/render-windows.ps1") -Raw
if ($render -notmatch 'SaveAs\(\$candidate,\s*32\)') {
    throw "render-windows.ps1 must use PowerPoint ppSaveAsPDF constant 32."
}
if ($render -notmatch "verify_pdf_fonts.py") {
    throw "render-windows.ps1 must run PDF font verification."
}

$powerPointCall = $render.IndexOf('if (Render-WithPowerPoint)')
$libreOfficeCall = $render.IndexOf('if (Render-WithLibreOffice)')
if ($powerPointCall -lt 0 -or $libreOfficeCall -lt 0 -or $powerPointCall -gt $libreOfficeCall) {
    throw "Windows rendering must prefer PowerPoint and use LibreOffice as fallback."
}

$deps = Get-Content (Join-Path $RepoRoot "deck/scripts/deps-windows.ps1") -Raw
if ($deps -notmatch 'TheDocumentFoundation\.LibreOffice') {
    throw "deps-windows.ps1 must guide or install the LibreOffice renderer."
}

Write-Output "windows script static checks passed"
