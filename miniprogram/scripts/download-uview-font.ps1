# 下载 uview-plus 字体文件到本地
# 用于替换阿里云 CDN 字体，避免外部请求

$fontUrl = "https://at.alicdn.com/t/font_2225171_8kdcwk4po24.ttf"
$outputDir = "src/static/fonts"
$outputFile = "$outputDir/uview-iconfont.ttf"

# 确保目录存在
if (-not (Test-Path $outputDir)) {
    New-Item -ItemType Directory -Path $outputDir -Force | Out-Null
    Write-Host "创建目录: $outputDir"
}

# 下载字体文件
Write-Host "正在下载 uview-plus 字体文件..."
try {
    Invoke-WebRequest -Uri $fontUrl -OutFile $outputFile -UseBasicParsing
    Write-Host "✅ 字体文件下载成功: $outputFile"
    Write-Host ""
    Write-Host "下一步："
    Write-Host "1. 确保 App.vue 中已配置使用本地字体（已完成）"
    Write-Host "2. 重新编译小程序"
    Write-Host "3. 检查网络请求，确认不再请求阿里云字体"
} catch {
    Write-Host "❌ 下载失败: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "请手动下载字体文件："
    Write-Host "URL: $fontUrl"
    Write-Host "保存到: $outputFile"
}

