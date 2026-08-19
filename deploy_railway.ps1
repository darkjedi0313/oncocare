# OncoCare Railway 배포 스크립트
# 사용법: 아래 RAILWAY_TOKEN 값을 채운 후 PowerShell에서 실행
# (Claude Code 외부 PowerShell에서 실행 — railway login 완료 후 또는 토큰 방식)

param(
    [string]$Token = ""
)

$ErrorActionPreference = "Stop"
$projectDir = "C:\Users\USER\project_ys\oncare"
$projectId  = "db9cd5d3-7208-40f1-bc0a-97bc5da6c78a"
$envId      = "e63e6e69-7f67-455a-b7db-e334b2ed69c7"

# PATH 갱신
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" +
            [System.Environment]::GetEnvironmentVariable("Path","User")

if ($Token) { $env:RAILWAY_TOKEN = $Token }

Set-Location $projectDir

Write-Host ""
Write-Host "=== [1/4] Railway 인증 확인 ===" -ForegroundColor Cyan
railway whoami
if ($LASTEXITCODE -ne 0) { Write-Host "인증 실패. 토큰을 확인하세요." -ForegroundColor Red; exit 1 }

Write-Host ""
Write-Host "=== [2/4] 프로젝트 연결 ===" -ForegroundColor Cyan
railway link --project $projectId --environment $envId
if ($LASTEXITCODE -ne 0) { Write-Host "프로젝트 연결 실패." -ForegroundColor Red; exit 1 }

Write-Host ""
Write-Host "=== [3/4] 환경변수 확인 ===" -ForegroundColor Cyan
Write-Host "  ▶ Railway 대시보드에서 아래 환경변수를 반드시 설정하세요:"
Write-Host "    GEMINI_API_KEY  = (실제 키 입력)"
Write-Host "    GEMINI_MODEL_NAME = gemini-3.6-flash"
Write-Host "    CORS_ORIGINS    = *"

Write-Host ""
Write-Host "=== [4/4] 배포 시작 ===" -ForegroundColor Cyan
Write-Host "  data/processed/ 포함, pipeline/ analysis/ tests/ 제외"
railway up --detach
if ($LASTEXITCODE -ne 0) { Write-Host "배포 실패." -ForegroundColor Red; exit 1 }

Write-Host ""
Write-Host "✓ 배포 완료! Railway 대시보드에서 빌드 로그를 확인하세요." -ForegroundColor Green
Write-Host "  URL: https://railway.com/project/$projectId"
