<#
.SYNOPSIS
    PowerShell wrapper for Microsoft MarkItDown CLI.
.DESCRIPTION
    Converts PDF, Word, Excel, PowerPoint, HTML, CSV, JSON, XML, Audio, Image, and ZIP files to Markdown.
.PARAMETER InputPath
    Path to file or directory to convert, or URL.
.PARAMETER OutputPath
    Optional path to save Markdown output. If omitted, writes to stdout or default directory.
.PARAMETER UseDocIntel
    Enable Azure Document Intelligence backend.
.PARAMETER DocIntelEndpoint
    Endpoint for Azure Document Intelligence (or via $env:MARKITDOWN_DOCINTEL_ENDPOINT).
.PARAMETER KeepDataUris
    Keep data URIs (e.g. base64-encoded images) inline instead of truncating.
.PARAMETER Recurse
    When InputPath is a folder, recursively convert all supported files.
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true, Position = 0)]
    [string]$InputPath,

    [Parameter(Position = 1)]
    [string]$OutputPath,

    [switch]$UseDocIntel,
    [string]$DocIntelEndpoint,
    [switch]$KeepDataUris,
    [switch]$Recurse
)

$env:PYTHONWARNINGS = "ignore"

function Convert-SingleFile {
    param([string]$FilePath, [string]$OutFile)
    
    $argsList = @()
    if ($UseDocIntel) {
        $argsList += "-d"
        $endpoint = if ($DocIntelEndpoint) { $DocIntelEndpoint } else { $env:MARKITDOWN_DOCINTEL_ENDPOINT }
        if ($endpoint) {
            $argsList += @("-e", $endpoint)
        }
    }
    if ($KeepDataUris) {
        $argsList += "--keep-data-uris"
    }

    $argsList += $FilePath

    if ($OutFile) {
        $outDir = Split-Path -Path $OutFile -Parent
        if ($outDir -and -not (Test-Path $outDir)) {
            New-Item -ItemType Directory -Path $outDir -Force | Out-Null
        }
        $argsList += @("-o", $OutFile)
        & markitdown @argsList
        if ($LASTEXITCODE -eq 0) {
            Write-Host "[OK] Converted '$FilePath' -> '$OutFile'" -ForegroundColor Green
        } else {
            Write-Error "Failed to convert '$FilePath'"
        }
    } else {
        & markitdown @argsList
    }
}

if ($InputPath -match '^https?://') {
    $argsList = @($InputPath)
    if ($OutputPath) {
        $argsList += @("-o", $OutputPath)
    }
    & markitdown @argsList
    exit $LASTEXITCODE
}

if (-not (Test-Path $InputPath)) {
    Write-Error "File or directory not found: $InputPath"
    exit 1
}

$item = Get-Item $InputPath
if ($item.PSIsContainer) {
    $supportedExts = @('.pdf', '.docx', '.pptx', '.xlsx', '.xls', '.html', '.htm', '.csv', '.json', '.xml', '.zip', '.epub', '.jpg', '.jpeg', '.png', '.gif', '.wav', '.mp3')
    $files = if ($Recurse) {
        Get-ChildItem -Path $InputPath -Recurse -File | Where-Object { $supportedExts -contains $_.Extension.ToLower() }
    } else {
        Get-ChildItem -Path $InputPath -File | Where-Object { $supportedExts -contains $_.Extension.ToLower() }
    }

    if (-not $OutputPath) {
        $OutputPath = Join-Path $InputPath "markdown_output"
    }

    foreach ($file in $files) {
        $relPath = if ($Recurse) {
            $file.FullName.Substring($item.FullName.Length).TrimStart('\', '/')
        } else {
            $file.Name
        }
        $targetFile = [System.IO.Path]::ChangeExtension((Join-Path $OutputPath $relPath), ".md")
        Convert-SingleFile -FilePath $file.FullName -OutFile $targetFile
    }
} else {
    Convert-SingleFile -FilePath $item.FullName -OutFile $OutputPath
}
