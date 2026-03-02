"""인증 API 테스트"""


class TestLogin:
    """로그인 테스트"""

    def test_login_success(self, client, auth_headers):
        """로그인 성공 테스트"""
        response = client.post("/api/auth/login", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Login successful"
        assert data["user"]["uid"] == "test-user-uid"
        assert data["user"]["email"] == "test@example.com"

    def test_login_creates_user_in_db(self, client, auth_headers):
        """로그인 시 DB에 사용자 생성 테스트"""
        # 첫 번째 로그인 - 신규 사용자
        response1 = client.post("/api/auth/login", headers=auth_headers)
        assert response1.status_code == 200
        assert response1.json()["user"]["is_new_user"] == True

        # 두 번째 로그인 - 기존 사용자
        response2 = client.post("/api/auth/login", headers=auth_headers)
        assert response2.status_code == 200
        assert response2.json()["user"]["is_new_user"] == False


class TestGetMe:
    """내 정보 조회 테스트"""

    def test_get_me_after_login(self, client, auth_headers):
        """로그인 후 내 정보 조회 테스트"""
        # 먼저 로그인
        client.post("/api/auth/login", headers=auth_headers)

        # 내 정보 조회
        response = client.get("/api/auth/me", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["uid"] == "test-user-uid"
        assert data["email"] == "test@example.com"
        assert data["name"] == "Test User"

    def test_get_me_without_login(self, client, auth_headers):
        """로그인하지 않은 사용자 정보 조회 (DB에 없음)"""
        # 로그인 없이 바로 조회 - Firebase 토큰 정보 반환
        response = client.get("/api/auth/me", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["uid"] == "test-user-uid"

