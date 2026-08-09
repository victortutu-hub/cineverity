param(
    [Parameter(Mandatory=$true)]
    [string]$ProjectId,

    [string]$Location = "global",

    [string]$Model = "gemini-3.5-flash"
)

$env:GOOGLE_CLOUD_PROJECT = $ProjectId
$env:GOOGLE_CLOUD_LOCATION = $Location
$env:GOOGLE_GENAI_USE_ENTERPRISE = "True"
$env:CINEVERITY_GEMINI_MODEL = $Model

Write-Host "CineVerity Google environment configured for this PowerShell session:"
Write-Host "  GOOGLE_CLOUD_PROJECT=$env:GOOGLE_CLOUD_PROJECT"
Write-Host "  GOOGLE_CLOUD_LOCATION=$env:GOOGLE_CLOUD_LOCATION"
Write-Host "  GOOGLE_GENAI_USE_ENTERPRISE=$env:GOOGLE_GENAI_USE_ENTERPRISE"
Write-Host "  CINEVERITY_GEMINI_MODEL=$env:CINEVERITY_GEMINI_MODEL"
