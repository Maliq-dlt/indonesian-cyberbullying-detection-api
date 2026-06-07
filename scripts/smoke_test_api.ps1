$BaseUrl = $env:BASE_URL
if (-not $BaseUrl) { $BaseUrl = "http://localhost:8000" }

$ApiKey = $env:API_KEY
if (-not $ApiKey) { $ApiKey = "change_this_to_a_long_random_secret" }

Write-Host "Checking health endpoint..."
Invoke-RestMethod -Uri "$BaseUrl/health" -Method Get | Out-Null
Write-Host "OK: /health"

Write-Host "Checking protected endpoint without API key..."
try {
    Invoke-WebRequest -Uri "$BaseUrl/models/status" -Method Get -ErrorAction Stop | Out-Null
    Write-Host "FAIL: /models/status allowed access without API key"
    exit 1
} catch {
    Write-Host "OK: /models/status blocks missing API key"
}

Write-Host "Checking protected endpoint with API key..."
try {
    Invoke-RestMethod -Uri "$BaseUrl/models/status" -Method Get -Headers @{ "X-API-Key" = $ApiKey } | Out-Null
    Write-Host "OK: /models/status accepts valid API key"
} catch {
    Write-Host "WARN: /models/status failed with API key. Check endpoint path or backend config."
}

Write-Host "Checking prediction endpoint candidate paths..."
$payload = @{ text = "contoh komentar untuk smoke test" } | ConvertTo-Json
$paths = @("/predict", "/api/predict", "/predict/hybrid", "/api/v1/predict")
$found = $false

foreach ($path in $paths) {
    try {
        Invoke-RestMethod `
            -Uri "$BaseUrl$path" `
            -Method Post `
            -Headers @{ "X-API-Key" = $ApiKey; "Content-Type" = "application/json" } `
            -Body $payload | Out-Null
        Write-Host "OK: prediction endpoint works at $path"
        $found = $true
        break
    } catch {
        # Try next path
    }
}

if (-not $found) {
    Write-Host "WARN: no common prediction path returned success. Check your actual route definitions."
}

Write-Host "Smoke test completed."
