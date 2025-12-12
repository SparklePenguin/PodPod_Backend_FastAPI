#!/bin/bash

# PodPod Backend - main 브랜치 최신 코드 동기화 스크립트

set -e

echo "🔄 Syncing with main branch..."
echo ""

# Git 저장소인지 확인
if [ ! -d ".git" ]; then
    echo "❌ Git 저장소가 아닙니다."
    exit 1
fi

# 현재 브랜치 확인
CURRENT_BRANCH=$(git branch --show-current)
echo "📍 현재 브랜치: $CURRENT_BRANCH"

# 변경사항이 있는지 확인
if ! git diff-index --quiet HEAD --; then
    echo ""
    echo "⚠️  커밋되지 않은 변경사항이 있습니다:"
    echo ""
    git status --short
    echo ""
    read -p "변경사항을 stash하고 계속하시겠습니까? (y/n): " -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "📦 Stashing changes..."
        git stash push -m "Auto-stash before sync-main at $(date)"
        STASHED=true
    else
        echo "❌ 동기화가 취소되었습니다."
        exit 0
    fi
fi

# main 브랜치로 전환
if [ "$CURRENT_BRANCH" != "main" ]; then
    echo ""
    echo "🔀 Switching to main branch..."
    git checkout main
fi

# SSH 세션에서 키체인 접근을 위해 unlock
echo ""
echo "🔓 Unlocking keychain..."
security unlock-keychain

# 원격 저장소에서 최신 코드 가져오기
echo ""
echo "📥 Fetching latest changes from origin..."
git fetch origin main

# 로컬 main 브랜치를 origin/main과 동기화
echo ""
echo "🔄 Pulling latest changes..."
git pull origin main

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ main 브랜치가 최신 상태로 업데이트되었습니다!"

    # 최근 커밋 로그 표시
    echo ""
    echo "📋 최근 커밋:"
    git log --oneline -5

    # stash한 변경사항이 있으면 복원 제안
    if [ "$STASHED" = true ]; then
        echo ""
        read -p "Stash한 변경사항을 복원하시겠습니까? (y/n): " -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            git stash pop
            echo "✅ 변경사항이 복원되었습니다."
        else
            echo "📦 변경사항은 stash에 저장되어 있습니다."
            echo "   복원하려면: git stash pop"
        fi
    fi
else
    echo ""
    echo "❌ Pull 실패"
    exit 1
fi

echo ""
