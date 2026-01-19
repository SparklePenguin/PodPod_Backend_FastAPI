# 신규 개발자 서버 접근 가이드

## 1️⃣ 로컬에서 SSH 키 생성

```bash
# ed25519 키 생성, 이메일 주석 추가
ssh-keygen -t ed25519 -C "developer@example.com"
```

*   메시지가 뜨면 기본 위치 사용 (엔터)
*   패스프레이즈는 필요하면 입력, 없으면 엔터

기본 생성 경로: `~/.ssh/id_ed25519` (개인키), `~/.ssh/id_ed25519.pub` (공개키)

**공개키(.pub)를 서버에 전달**

## 2️⃣ 서버 개발자에게 공개키 전달

**공개키 확인**

```bash
cat ~/.ssh/id_ed25519.pub
```

서버 개발자에게 안전하게 전달 (이메일, 슬랙, 안전한 공유 폴더 등)

## 3️⃣ 로컬 SSH 프로필 설정 (선택)

`~/.ssh/config`에 서버 별 프로필 추가

```
Host dev-server
    HostName server.example.com
    User developer
    IdentityFile ~/.ssh/id_ed25519
```

이제 접속할 때:

```bash
ssh dev-server
```

비밀번호 없이 바로 접속 가능
