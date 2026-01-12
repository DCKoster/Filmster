# Filmster - Complete Pipeline Runner
# This script runs all steps of the poster preparation pipeline

param(
    [string[]]$Urls = @(),
    [switch]$ForceRefresh
)

# ============================================================
# CONFIGURATION - Edit URLs here
# ============================================================
# If no URLs provided as arguments, use these defaults:
$DefaultUrls = @(
    "https://www.imdb.com/chart/top/"
    "https://www.imdb.com/list/ls098063263"
    "https://www.imdb.com/list/ls055265443"
    # "https://www.imdb.com/chart/toptv/"
)
# ============================================================

Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "FILMSTER - COMPLETE PIPELINE" -ForegroundColor Cyan
Write-Host "============================================================`n" -ForegroundColor Cyan

# Determine which URLs to use
$scrapeArgs = @()

if ($Urls.Count -gt 0) {
    $scrapeArgs += "--urls"
    $scrapeArgs += $Urls
    Write-Host "Using provided URLs:" -ForegroundColor Cyan
    foreach ($url in $Urls) {
        Write-Host "  - $url" -ForegroundColor Gray
    }
}
else {
    $scrapeArgs += "--urls"
    $scrapeArgs += $DefaultUrls
    Write-Host "Using default URLs:" -ForegroundColor Cyan
    foreach ($url in $DefaultUrls) {
        Write-Host "  - $url" -ForegroundColor Gray
    }
}

if ($ForceRefresh) {
    $scrapeArgs += "--force-refresh"
    Write-Host "`nForce refresh enabled (ignoring cache)" -ForegroundColor Yellow
}

Write-Host ""

# Step 1: Scrape movie list
Write-Host "STEP 1: Scraping movie lists..." -ForegroundColor Yellow
.venv\Scripts\python.exe prepare_posters.py @scrapeArgs
if ($LASTEXITCODE -ne 0) {
    Write-Host "`nError in Step 1: Scraping failed" -ForegroundColor Red
    exit 1
}

Write-Host "`n`nPress Enter to continue to Step 2..." -ForegroundColor Green
Read-Host

# Step 2: Download posters
Write-Host "`nSTEP 2: Downloading posters..." -ForegroundColor Yellow
.venv\Scripts\python.exe prepare_posters.py --download
if ($LASTEXITCODE -ne 0) {
    Write-Host "`nError in Step 2: Download failed" -ForegroundColor Red
    exit 1
}

Write-Host "`n`nPress Enter to continue to Step 3..." -ForegroundColor Green
Read-Host

# Step 3: Process posters (detect and blur titles)
Write-Host "`nSTEP 3: Processing posters (detecting and blurring titles)..." -ForegroundColor Yellow
.venv\Scripts\python.exe prepare_posters.py --process
if ($LASTEXITCODE -ne 0) {
    Write-Host "`nError in Step 3: Processing failed" -ForegroundColor Red
    exit 1
}

Write-Host "`n`nPress Enter to continue to Step 4..." -ForegroundColor Green
Read-Host

# Step 4: Sample for game
Write-Host "`nSTEP 4: Sampling posters for game..." -ForegroundColor Yellow
.venv\Scripts\python.exe prepare_posters.py --sample
if ($LASTEXITCODE -ne 0) {
    Write-Host "`nError in Step 4: Sampling failed" -ForegroundColor Red
    exit 1
}

# Complete
Write-Host "`n`n============================================================" -ForegroundColor Cyan
Write-Host "PIPELINE COMPLETE!" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "`nGame posters are ready in: game/posters/" -ForegroundColor Green
Write-Host "Check list/ folder for detailed logs`n" -ForegroundColor Green
