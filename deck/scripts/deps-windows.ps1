param(
  [switch]$Check,
  [switch]$Install,
  [switch]$Python
)

$ErrorActionPreference = 'Stop'
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$SkillDir = Split-Path -Parent $ScriptDir
$DeckHome = if ($env:DECK_HOME) { $env:DECK_HOME } elseif ($env:XDG_DATA_HOME) { Join-Path $env:XDG_DATA_HOME 'claude-deck-skill' } else { Join-Path $env:LOCALAPPDATA 'claude-deck-skill' }
$DeckVenv = Join-Path $DeckHome 'venv'
$DeckPython = Join-Path $DeckVenv 'Scripts\python.exe'
$ReqFile = Join-Path $SkillDir 'requirements.txt'
$FontSourceDir = Join-Path $SkillDir 'assets\fonts'
$FontTargetDir = Join-Path $env:LOCALAPPDATA 'Microsoft\Windows\Fonts'

function Get-PythonCommand {
  if (Get-Command py -ErrorAction SilentlyContinue) { return (Get-Command py).Source }
  if (Get-Command python -ErrorAction SilentlyContinue) { return (Get-Command python).Source }
  throw 'Python 3 is missing. Install Python 3 with the py launcher, then rerun -Install.'
}

function Test-PythonEnv {
  if (-not (Test-Path $DeckPython)) { return $false }
  & $DeckPython -c "import pptx, PIL, pypdf" *> $null
  return $LASTEXITCODE -eq 0
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

function Test-Renderer {
  if (Find-LibreOffice) { return $true }
  return [bool][type]::GetTypeFromProgID('PowerPoint.Application')
}

function Test-Fonts {
  $regular = Join-Path $FontTargetDir 'Pretendard-Regular.otf'
  $bold = Join-Path $FontTargetDir 'Pretendard-Bold.otf'
  $fontsKey = 'HKCU:\Software\Microsoft\Windows NT\CurrentVersion\Fonts'
  if (-not (Test-Path $regular) -or -not (Test-Path $bold) -or -not (Test-Path $fontsKey)) {
    return $false
  }
  $values = Get-ItemProperty -Path $fontsKey
  return ($values.'Pretendard Regular (OpenType)' -eq 'Pretendard-Regular.otf') -and
    ($values.'Pretendard Bold (OpenType)' -eq 'Pretendard-Bold.otf')
}

function Install-Fonts {
  foreach ($name in @('Pretendard-Regular.otf', 'Pretendard-Bold.otf')) {
    if (-not (Test-Path (Join-Path $FontSourceDir $name))) {
      throw "Bundled font is missing: $name"
    }
  }
  New-Item -ItemType Directory -Force -Path $FontTargetDir | Out-Null
  Copy-Item -Force (Join-Path $FontSourceDir 'Pretendard-Regular.otf') $FontTargetDir
  Copy-Item -Force (Join-Path $FontSourceDir 'Pretendard-Bold.otf') $FontTargetDir
  $fontsKey = 'HKCU:\Software\Microsoft\Windows NT\CurrentVersion\Fonts'
  New-Item -Path $fontsKey -Force | Out-Null
  New-ItemProperty -Path $fontsKey -Name 'Pretendard Regular (OpenType)' -Value 'Pretendard-Regular.otf' -PropertyType String -Force | Out-Null
  New-ItemProperty -Path $fontsKey -Name 'Pretendard Bold (OpenType)' -Value 'Pretendard-Bold.otf' -PropertyType String -Force | Out-Null
  Add-Type @"
using System;
using System.Runtime.InteropServices;
public static class DeckFontNative {
  [DllImport("gdi32.dll", CharSet = CharSet.Unicode, SetLastError = true)]
  public static extern int AddFontResourceEx(string lpszFilename, uint fl, IntPtr pdv);
  [DllImport("user32.dll", CharSet = CharSet.Unicode, SetLastError = true)]
  public static extern IntPtr SendMessageTimeout(IntPtr hWnd, uint Msg, UIntPtr wParam, string lParam, uint fuFlags, uint uTimeout, out UIntPtr lpdwResult);
}
"@
  $files = @(
    (Join-Path $FontTargetDir 'Pretendard-Regular.otf'),
    (Join-Path $FontTargetDir 'Pretendard-Bold.otf')
  )
  foreach ($file in $files) {
    [void][DeckFontNative]::AddFontResourceEx($file, 0, [IntPtr]::Zero)
  }
  $result = [UIntPtr]::Zero
  [void][DeckFontNative]::SendMessageTimeout([IntPtr]0xffff, 0x001D, [UIntPtr]::Zero, $null, 0x0002, 1000, [ref]$result)
}

function Check-Dependencies {
  $missing = @()
  if (Test-PythonEnv) {
    Write-Host 'READY    Python packages - python-pptx + Pillow + pypdf'
  } else {
    Write-Host 'MISSING  deck venv - python-pptx + Pillow + pypdf'
    $missing += 'python'
  }
  if (Test-Renderer) {
    Write-Host 'READY    renderer - PowerPoint or LibreOffice'
  } else {
    Write-Host 'MISSING  renderer - PowerPoint or LibreOffice'
    $missing += 'renderer'
  }
  if (Test-Fonts) {
    Write-Host 'READY    font - Pretendard installed'
  } else {
    Write-Host 'MISSING  font - Pretendard not installed in user fonts'
    $missing += 'font'
  }

  if ($missing.Count -gt 0) {
    Write-Host ''
    Write-Host 'Install is available after user approval:'
    Write-Host "  powershell -File `"$ScriptDir\deps-windows.ps1`" -Install"
    exit 1
  }

  Write-Host 'READY    deck skill is runnable'
}

function Install-Dependencies {
  $pythonCmd = Get-PythonCommand
  New-Item -ItemType Directory -Force -Path $DeckHome | Out-Null
  if (-not (Test-Path $DeckVenv)) {
    if ((Split-Path -Leaf $pythonCmd) -ieq 'py.exe') {
      & $pythonCmd -3 -m venv $DeckVenv
    } else {
      & $pythonCmd -m venv $DeckVenv
    }
    if ($LASTEXITCODE -ne 0) { throw 'Failed to create the deck Python environment.' }
  }
  & $DeckPython -m pip install --upgrade pip | Out-Null
  if ($LASTEXITCODE -ne 0) { throw 'Failed to upgrade pip.' }
  & $DeckPython -m pip install -r $ReqFile
  if ($LASTEXITCODE -ne 0) { throw 'Failed to install deck Python dependencies.' }
  Install-Fonts

  if (-not (Test-Renderer)) {
    $winget = Get-Command winget -ErrorAction SilentlyContinue
    if ($winget) {
      Write-Host 'Installing LibreOffice with winget because PowerPoint/LibreOffice is missing.'
      & $winget.Source install --exact --id TheDocumentFoundation.LibreOffice --accept-package-agreements --accept-source-agreements
      if ($LASTEXITCODE -ne 0) {
        Write-Warning 'winget could not install LibreOffice. Install PowerPoint or LibreOffice manually, then rerun -Check.'
      }
    } else {
      Write-Warning 'Renderer is still required. Install Microsoft PowerPoint or LibreOffice manually, then rerun -Check.'
    }
  }

  Check-Dependencies
}

if ($Check) {
  Check-Dependencies
} elseif ($Install) {
  Install-Dependencies
} elseif ($Python) {
  if (Test-PythonEnv) {
    Write-Output $DeckPython
  } else {
    throw "Run powershell -File `"$ScriptDir\deps-windows.ps1`" -Install first."
  }
} else {
  Write-Host 'Usage: powershell -File deps-windows.ps1 -Check|-Install|-Python'
  exit 2
}
