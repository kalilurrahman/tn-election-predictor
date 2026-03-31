# Safe Hugging Face deployment helper for the TN Election Predictor
param(
    [string]$Username = "your-username",
    [string]$SpaceName = "tn-election-predictor"
)

Write-Host "--- Hugging Face Space Push Helper ---" -ForegroundColor Cyan

$hfUrl = "https://huggingface.co/spaces/$Username/$SpaceName"
$remotes = git remote

if ($remotes -notcontains "hf") {
    Write-Host "Adding Hugging Face remote: $hfUrl" -ForegroundColor Yellow
    git remote add hf $hfUrl
}

Write-Host "Staging current project changes..." -ForegroundColor Gray
git add .

Write-Host "Creating deployment commit if needed..." -ForegroundColor Gray
git commit -m "Deploy election predictor to Hugging Face Space"

Write-Host "Pushing to Hugging Face Space..." -ForegroundColor Green
git push hf main
