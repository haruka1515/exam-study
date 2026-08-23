# Minimal static file server for local preview.
#
# The site uses fetch() and ES modules, both of which browsers block on
# file:// — so opening index.html by double-click will not work. This serves
# the repo over http instead, using only what ships with Windows: no Node,
# no Python, no install, no admin rights.
#
#   powershell -ExecutionPolicy Bypass -File tools\serve.ps1
#   powershell -ExecutionPolicy Bypass -File tools\serve.ps1 -Port 3000
#
# Ctrl+C to stop.

param(
    [int]$Port = 8080,
    [switch]$NoBrowser
)

$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent

$mime = @{
    '.html' = 'text/html; charset=utf-8'
    '.css'  = 'text/css; charset=utf-8'
    '.js'   = 'text/javascript; charset=utf-8'
    '.mjs'  = 'text/javascript; charset=utf-8'
    '.json' = 'application/json; charset=utf-8'
    '.md'   = 'text/plain; charset=utf-8'
    '.svg'  = 'image/svg+xml'
    '.png'  = 'image/png'
    '.jpg'  = 'image/jpeg'
    '.ico'  = 'image/x-icon'
    '.woff2' = 'font/woff2'
}

$listener = New-Object System.Net.HttpListener
$listener.Prefixes.Add("http://localhost:$Port/")

try {
    $listener.Start()
}
catch {
    Write-Host "Could not listen on port $Port. Try another: -Port 3000" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor DarkGray
    exit 1
}

Write-Host ""
Write-Host "  Serving $root" -ForegroundColor DarkGray
Write-Host "  http://localhost:$Port" -ForegroundColor Cyan
Write-Host "  Ctrl+C to stop" -ForegroundColor DarkGray
Write-Host ""

if (-not $NoBrowser) { Start-Process "http://localhost:$Port" }

try {
    while ($listener.IsListening) {
        $context = $listener.GetContext()
        $req = $context.Request
        $res = $context.Response

        # Decode, strip query, normalise separators, default to index.html.
        $rel = [Uri]::UnescapeDataString($req.Url.AbsolutePath).TrimStart('/')
        if ([string]::IsNullOrWhiteSpace($rel)) { $rel = 'index.html' }
        $rel = $rel -replace '/', '\'

        $path = Join-Path $root $rel
        $full = [System.IO.Path]::GetFullPath($path)

        # Refuse anything that escapes the repo root (../.. traversal).
        if (-not $full.StartsWith([System.IO.Path]::GetFullPath($root), [StringComparison]::OrdinalIgnoreCase)) {
            $res.StatusCode = 403
            $res.Close()
            continue
        }

        if (Test-Path -LiteralPath $full -PathType Container) {
            $full = Join-Path $full 'index.html'
        }

        if (Test-Path -LiteralPath $full -PathType Leaf) {
            $bytes = [System.IO.File]::ReadAllBytes($full)
            $ext = [System.IO.Path]::GetExtension($full).ToLowerInvariant()
            $res.ContentType = if ($mime.ContainsKey($ext)) { $mime[$ext] } else { 'application/octet-stream' }
            $res.Headers.Add('Cache-Control', 'no-cache')
            $res.ContentLength64 = $bytes.Length
            $res.OutputStream.Write($bytes, 0, $bytes.Length)
            $code = 200
        }
        else {
            $body = [System.Text.Encoding]::UTF8.GetBytes("404 - $rel not found")
            $res.StatusCode = 404
            $res.ContentType = 'text/plain; charset=utf-8'
            $res.ContentLength64 = $body.Length
            $res.OutputStream.Write($body, 0, $body.Length)
            $code = 404
        }

        $colour = if ($code -eq 200) { 'DarkGray' } else { 'Yellow' }
        Write-Host ("  {0}  {1}" -f $code, $req.Url.AbsolutePath) -ForegroundColor $colour
        $res.Close()
    }
}
finally {
    $listener.Stop()
    $listener.Close()
    Write-Host "`n  Stopped." -ForegroundColor DarkGray
}
