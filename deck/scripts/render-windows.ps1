param(
  [Parameter(Mandatory = $true)][string]$InputPath,
  [string]$OutputPath
)

$ErrorActionPreference = 'Stop'
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$SkillDir = Split-Path -Parent $ScriptDir
$ShellExe = if ($PSVersionTable.PSEdition -eq 'Core') { Join-Path $PSHOME 'pwsh.exe' } else { Join-Path $PSHOME 'powershell.exe' }
$DeckPython = & $ShellExe -NoProfile -File (Join-Path $ScriptDir 'deps-windows.ps1') -Python
if (-not $OutputPath) {
  $OutputPath = [System.IO.Path]::ChangeExtension($InputPath, '.pdf')
}

$InputFull = [System.IO.Path]::GetFullPath($InputPath)
$OutputFull = [System.IO.Path]::GetFullPath($OutputPath)
if (-not (Test-Path $InputFull)) { throw "Missing PPTX: $InputFull" }
$OutputDir = Split-Path -Parent $OutputFull
New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null
$TempRoot = [System.IO.Path]::GetTempPath()
$JobDir = Join-Path $TempRoot ("deck-render-{0}" -f ([System.Guid]::NewGuid().ToString('N')))
New-Item -ItemType Directory -Force -Path $JobDir | Out-Null

function Invoke-Verify([string]$PdfPath) {
  $verify = Join-Path $SkillDir 'scripts\verify_pdf_fonts.py'
  if (-not (Test-Path $verify)) { throw "Missing verifier: $verify" }
  & $DeckPython $verify $InputFull $PdfPath
  if ($LASTEXITCODE -ne 0) { throw 'PDF font verification failed.' }
}

function Find-LibreOffice {
  $command = Get-Command soffice.com -ErrorAction SilentlyContinue
  if (-not $command) { $command = Get-Command soffice.exe -ErrorAction SilentlyContinue }
  if (-not $command) { $command = Get-Command soffice -ErrorAction SilentlyContinue }
  if ($command) { return $command.Source }
  $candidates = @()
  if ($env:ProgramFiles) {
    $candidates += Join-Path $env:ProgramFiles 'LibreOffice\program\soffice.com'
  }
  $programFilesX86 = [Environment]::GetEnvironmentVariable('ProgramFiles(x86)')
  if ($programFilesX86) {
    $candidates += Join-Path $programFilesX86 'LibreOffice\program\soffice.com'
  }
  foreach ($candidate in $candidates) {
    if ($candidate -and (Test-Path $candidate)) { return $candidate }
  }
  return $null
}

function Render-WithLibreOffice {
  $soffice = Find-LibreOffice
  if (-not $soffice) { return $false }
  $profile = Join-Path $JobDir 'profile'
  $outDir = Join-Path $JobDir 'out'
  New-Item -ItemType Directory -Force -Path $profile, $outDir | Out-Null
  & $soffice "-env:UserInstallation=file:///$($profile -replace '\\','/')" --headless --convert-to pdf --outdir $outDir $InputFull *> $null
  $candidate = Join-Path $outDir ([System.IO.Path]::GetFileNameWithoutExtension($InputFull) + '.pdf')
  if (Test-Path $candidate) {
    Invoke-Verify $candidate
    Copy-Item -Force $candidate $OutputFull
    Write-Output $OutputFull
    return $true
  }
  return $false
}

function Render-WithPowerPoint {
  try {
    $app = New-Object -ComObject PowerPoint.Application
  } catch {
    return $false
  }

  try {
    $presentation = $app.Presentations.Open($InputFull, $true, $false, $false)
    # Microsoft docs: SaveAs file format 32 = PDF.
    $candidate = Join-Path $JobDir 'powerpoint.pdf'
    $presentation.SaveAs($candidate, 32)
    $presentation.Close()
    $app.Quit()
    if (Test-Path $candidate) {
      Invoke-Verify $candidate
      Copy-Item -Force $candidate $OutputFull
      Write-Output $OutputFull
      return $true
    }
    return $false
  } catch {
    try { $app.Quit() } catch {}
    return $false
  }
}

try {
  if (Render-WithPowerPoint) { exit 0 }
  if (Render-WithLibreOffice) { exit 0 }
  throw 'Render failed: neither LibreOffice nor PowerPoint could export the deck.'
} finally {
  if (Test-Path $JobDir) {
    Remove-Item -Recurse -Force $JobDir
  }
}
