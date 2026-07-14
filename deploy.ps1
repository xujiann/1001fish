# 1001fish one-click deploy. Run in your own terminal:
#   powershell -File C:\Users\drxuj\OneDrive\claude\1001fish\deploy.ps1
# Requires: gh auth login (currently xujiann). Creates two PUBLIC repos + enables Pages.
$ErrorActionPreference = 'Stop'
$root = 'C:/Users/drxuj/OneDrive/claude/1001fish'
$cdn  = 'https://cdn.jsdelivr.net/gh/xujiann/1001fish-img@v1/images'

Write-Host '== 1/5 stage image repo =='
$img = Join-Path $env:TEMP '1001fish-img'
if (Test-Path $img) { Remove-Item -Recurse -Force $img }
New-Item -ItemType Directory -Force (Join-Path $img 'images') | Out-Null
Copy-Item "$root/images/*" (Join-Path $img 'images') -Force
Set-Location $img
'1001fish images - served via jsDelivr CDN, paired with xujiann/1001fish' | Out-File -Encoding ascii README.md
git init -q
git checkout -q -b main
git add -A
git -c user.name="cosmos1001" -c user.email="popstudy@gmail.com" commit -q -m "1001 fish images (800px, from Wikimedia Commons)"

Write-Host '== 2/5 create image repo, push, tag v1 =='
gh repo create xujiann/1001fish-img --public --source=. --remote=origin --push
git tag v1
git push origin v1

Write-Host '== 3/5 switch frontend image base to jsDelivr CDN =='
$appjs = Join-Path $root 'app.js'
$content = Get-Content $appjs -Raw -Encoding UTF8
$content = $content.Replace('const IMG_BASE = "images";', ('const IMG_BASE = "' + $cdn + '";'))
[System.IO.File]::WriteAllText($appjs, $content, (New-Object System.Text.UTF8Encoding($false)))

Write-Host '== 4/5 create main repo and push (images/ gitignored) =='
Set-Location $root
if (-not (Test-Path (Join-Path $root '.git'))) {
  git init -q
  git checkout -q -b main
}
git add -A
git -c user.name="cosmos1001" -c user.email="popstudy@gmail.com" commit -q -m "1001 Fishes - bilingual gallery (1001 species, real photos)"
gh repo create xujiann/1001fish --public --source=. --remote=origin --push

Write-Host '== 5/5 enable GitHub Pages =='
try {
  gh api -X POST 'repos/xujiann/1001fish/pages' -f 'source[branch]=main' -f 'source[path]=/' | Out-Null
} catch {
  Write-Host '   (Pages may already be on, or enable it in repo Settings > Pages)'
}

Write-Host ''
Write-Host 'DONE. Live in a minute or two: https://xujiann.github.io/1001fish/'
Write-Host '(jsDelivr may take 1-2 min to cache the v1 tag on first hit)'
