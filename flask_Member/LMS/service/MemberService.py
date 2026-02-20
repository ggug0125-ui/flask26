from LMS.common.session import Session
from LMS.domain.Member import Member


class MemberService:
    """
    MemberService는 DB연결 + DB저장 + 예외처리 + 중복체크 + 조회/수정 + 마이페이지 계산 처리
    Flask session 저장/관리는 app.py에서 담당 (여기서는 member 객체 반환만)
    """

    @staticmethod
    def exists_uid(uid: str) -> bool:      # 아이디 중복체크
        conn = Session.get_connection()

        try:
            with conn.cursor() as cursor:
                sql = "SELECT 1 FROM members WHERE uid=%s LIMIT 1"
                cursor.execute(sql, (uid,))
                row = cursor.fetchone()
                return True if row else False
        finally:
            conn.close()

    @staticmethod
    def join(uid, password, name):         # 회원가입
        """
        회원가입:
        - uid 중복 체크
        - role은 무조건 'user'로 강제
        """
        if not uid:
            return False, "아이디를 입력하세요."
        if not password:
            return False, "비밀번호를 입력하세요."
        conn = Session.get_connection()
        try:
            with conn.cursor() as cursor:
                if MemberService.exists_uid(uid):
                    return False, "이미 존재하는 아이디입니다."
                sql = """
                    INSERT INTO members (uid, password, name, role)
                    VALUES (%s, %s, %s, %s)
                """
                cursor.execute(sql, (uid, password, name, 'user'))
            conn.commit()
            return True, "회원가입이 완료되었습니다."
        except Exception as e:
            print(f"회원가입 에러: {e}")
            return False, "가입 중 오류가 발생했습니다."
        finally:
            conn.close()

    @staticmethod
    def login(uid, password):                # 로그인
        """
        로그인:
        - DB에서 uid/pw/active 확인
        - 성공 시 Member 객체 반환
        - 세션 저장은 app.py에서 처리
        """
        conn = Session.get_connection()
        try:
            with conn.cursor() as cursor:
                sql = "SELECT * FROM members WHERE uid=%s AND password=%s AND active=1"
                cursor.execute(sql, (uid, password))
                row = cursor.fetchone()
                if row:
                    member = Member.from_db(row)
                    return True, member
                return False, None
        except Exception as e:
            print(f"로그인 에러: {e}")
            return False, None
        finally:
            conn.close()

    @staticmethod
    def edit_member(member_id, new_name, new_password, new_role=None):   #회원정보수정
        """
        회원정보 수정:
        - new_password가 비어있으면 비번 변경 X
        - new_role이 None이면 role 변경 X
        ⚠️ 권한 체크(일반유저가 role 보내는 것)는 app.py에서 막아야 안전
        """
        conn = Session.get_connection()
        try:
            with conn.cursor() as cursor:
                if new_password:  # 비번 변경 O
                    if new_role:  # 권한 변경 O
                        sql = "UPDATE members SET name=%s, password=%s, role=%s WHERE id=%s"
                        cursor.execute(sql, (new_name, new_password, new_role, member_id))
                    else:  # 권한 변경 X
                        sql = "UPDATE members SET name=%s, password=%s WHERE id=%s"
                        cursor.execute(sql, (new_name, new_password, member_id))
                else:  # 비번 변경 X
                    if new_role:  # 권한 변경 O
                        sql = "UPDATE members SET name=%s, role=%s WHERE id=%s"
                        cursor.execute(sql, (new_name, new_role, member_id))
                    else:  # 권한 변경 X
                        sql = "UPDATE members SET name=%s WHERE id=%s"
                        cursor.execute(sql, (new_name, member_id))
            conn.commit()
            return True, "회원정보가 수정되었습니다."

        except Exception as e:
            print(f"회원정보 수정 에러: {e}")
            return False, "수정 중 오류가 발생했습니다."
        finally:
            conn.close()

    @staticmethod
    def get_mypage(member_id):                   # 내정보 보기
        """
        마이페이지:
        - members 조회 후 Member 객체로 변환해서 반환 (템플릿에서 user.name 방식 가능)
        - boards 테이블 없을 수도 있으니 count는 try/except로 안전 처리
        """
        conn = Session.get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM members WHERE id=%s", (member_id,))
                user_row = cursor.fetchone()
                if not user_row:
                    return None, 0
                user = Member.from_db(user_row)
                try:
                    cursor.execute(
                        "SELECT COUNT(*) AS board_count FROM boards WHERE member_id=%s",
                        (member_id,)
                    )
                    board_count = cursor.fetchone().get('board_count', 0)
                except Exception:
                    board_count = 0
                return user, board_count
        except Exception as e:
            print(f"마이페이지 조회 에러: {e}")
            return None, 0
        finally:
            conn.close()

    @staticmethod
    def list_members():                      # 관리자메뉴 (회원리스트)
        """관리자용: 전체 회원 목록 조회"""
        conn = Session.get_connection()
        try:
            with conn.cursor() as cursor:
                sql = """
                        SELECT id, uid, name, role, active, created_at
                        FROM members
                        ORDER BY id ASC
                    """
                cursor.execute(sql)
                rows = cursor.fetchall()
                members = []
                for row in rows:
                    m = Member.from_db(row)
                    m.created_at = row.get('created_at')
                    members.append(m)
                return members
        finally:
            conn.close()

    @staticmethod
    def update_role(target_member_id, new_role):  # 관리자 (권한변경)
        """관리자/매니저용: 회원 권한 변경"""
        if new_role not in ('user', 'manager', 'admin'):
            return False, "잘못된 권한 값입니다."

        conn = Session.get_connection()
        try:
            with conn.cursor() as cursor:
                sql = "UPDATE members SET role=%s WHERE id=%s"
                cursor.execute(sql, (new_role, target_member_id))
            conn.commit()
            return True, "권한이 변경되었습니다."
        except Exception as e:
            print(f"권한 변경 에러: {e}")
            return False, "권한 변경 중 오류가 발생했습니다."
        finally:
            conn.close()

    @staticmethod
    def set_active(member_id, active):     # 관리자 (비활성화)
        """
        회원 활성/비활성 처리
        active = 1 (활성)
        active = 0 (정지)
        """
        conn = Session.get_connection()
        try:
            with conn.cursor() as cursor:
                sql = "UPDATE members SET active=%s WHERE id=%s"
                cursor.execute(sql, (active, member_id))
            conn.commit()

            if active:
                return True, "회원이 활성화되었습니다."
            else:
                return True, "회원이 정지되었습니다."

        except Exception as e:
            print(f"회원 활성 변경 에러: {e}")
            return False, "처리 중 오류가 발생했습니다."
        finally:
            conn.close()
