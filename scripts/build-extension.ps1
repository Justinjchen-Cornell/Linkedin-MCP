Set-Location $PSScriptRoot\..\extension
npm install
npm run build
Write-Host "扩展已构建：extension/dist。请在 Edge 扩展页加载这个目录。"
