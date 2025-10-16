Param(
  [Parameter(Mandatory=$true)]
  [string]$RepoUrl
)

git init
git remote add origin $RepoUrl
git add .
git commit -m "init: ai intelligence hub with alerts + actions"
git branch -M main
git push -u origin main
Write-Host "✅ 已推送到 $RepoUrl"
