from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from LMS.service import MemberService
from LMS.service.BoardService import BoardService
from LMS.common import Session

app = Flask(__name__)
app.secret_key = "fffffff"

# app.py는 라우팅 + 템플릿 + 세션 업데이트 담당

@app.route('/')
def index():
    return render_template('main.html')


@app.route('/join', methods=['GET', 'POST'])
def join():                                  # 회원가입
    if request.method == 'GET':
        return render_template('join.html')

    uid_raw = request.form.get('uid', '')
    uid = uid_raw.strip()

    password_raw = request.form.get('password', '')
    password = password_raw.strip()

    name_raw = request.form.get('name', '')
    name = name_raw.strip()

    if not uid:
        return "<script>alert('아이디(uid)가 없습니다. 회원가입 폼에 uid 입력칸이 필요합니다.'); history.back();</script>"
    if not password:
        return "<script>alert('비밀번호를 입력하세요.'); history.back();</script>"
    if not name:
        return "<script>alert('이름을 입력하세요.'); history.back();</script>"

    success, message = MemberService.join(uid, password, name)
    if success:
        return f"<script>alert('{message}'); location.href='/login';</script>"
    return f"<script>alert('{message}'); history.back();</script>"

@app.get("/member/check-uid")
def member_check_uid():                 # 아이디 중복체크
    uid = (request.args.get("uid") or "").strip()
    if len(uid) < 3:
        return jsonify({
            "ok": False,
            "exists": False,
            "msg": "아이디는 3자 이상 입력하세요."
        })
        # 서버에서도 길이 검증

    exists = MemberService.exists_uid(uid)
    # DB 중복 체크

    return jsonify({
        "ok": True,
        "exists": exists
    })

@app.route('/login', methods=['GET', 'POST'])
def login():                              # 로그인
    if request.method == 'GET':
        return render_template('login.html')

    uid = request.form.get('uid', '').strip()
    password = request.form.get('password', '').strip()

    if not uid or not password:
        return "<script>alert('아이디/비밀번호를 입력하세요.');history.back();</script>"

    success, member = MemberService.login(uid, password)
    if success:
        # 세션 저장
        session['user_id'] = member.id
        session['user_name'] = member.name
        session['user_uid'] = member.uid
        session['user_role'] = member.role
        return redirect(url_for('index'))

    return "<script>alert('아이디나 비밀번호가 틀렸습니다.');history.back();</script>"


@app.route('/logout')
def logout():                              # 로그아웃
    session.clear()
    return redirect(url_for('login'))


@app.route('/member/edit', methods=['GET', 'POST'])
def member_edit():                         # 회원정보수정
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'GET':
        user_info, _ = MemberService.get_mypage(session['user_id'])
        return render_template('member_edit.html', user=user_info)

    new_name = request.form.get('name', '').strip()
    new_password = request.form.get('password', '').strip()

    new_role = None
    if session.get('user_role') in ('admin', 'manager'):
        role_from_form = request.form.get('role')
        if role_from_form in ('admin', 'manager', 'user'):
            new_role = role_from_form

    success, message = MemberService.edit_member(
        session['user_id'],
        new_name,
        new_password,
        new_role
    )

    if success:
        session['user_name'] = new_name
        if new_role:
            session['user_role'] = new_role
        return f"<script>alert('{message}'); location.href='/mypage';</script>"

    return f"<script>alert('{message}'); history.back();</script>"


@app.route('/mypage')
def mypage():                          # 내정보 보기
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user, board_count = MemberService.get_mypage(session['user_id'])
    return render_template('mypage.html', user=user, board_count=board_count)


def require_manager_or_admin():
    """관리/매니저 권한 체크(간단 함수)"""
    if session.get('user_role') not in ('admin', 'manager'):
        return False
    return True

@app.route('/admin/members')
def admin_members():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    if not require_manager_or_admin():
        return "<script>alert('권한이 없습니다.');history.back();</script>"

    members = MemberService.list_members()
    return render_template('admin_member_list.html', members=members)

@app.route('/admin/members/role', methods=['POST'])
def admin_member_role_update():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if not require_manager_or_admin():
        return "<script>alert('권한이 없습니다.');history.back();</script>"

    target_id = request.form.get('member_id', '').strip()
    new_role = request.form.get('role', '').strip()

    if not target_id.isdigit():
        return "<script>alert('잘못된 요청입니다.');history.back();</script>"

    if session.get("user_id") == int(target_id):
        return "<script>alert('자기 자신의 권한은 변경할 수 없습니다.');history.back();</script>"
    if new_role not in ('user', 'manager', 'admin'):
        return "<script>alert('잘못된 권한 값입니다.');history.back();</script>"

    success, msg = MemberService.update_role(int(target_id), new_role)
    if success:
        return f"<script>alert('{msg}'); location.href='/admin/members';</script>"
    return f"<script>alert('{msg}'); history.back();</script>"



@app.route('/admin/members/active', methods=['POST'])
def admin_member_active():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if session.get('user_role') not in ('admin', 'manager'):
        return "<script>alert('권한이 없습니다.');history.back();</script>"

    member_id = request.form.get('member_id')
    active = request.form.get('active')

    if not member_id or not active:
        return "<script>alert('잘못된 요청입니다.');history.back();</script>"

    success, msg = MemberService.set_active(int(member_id), int(active))

    if success:
        return f"<script>alert('{msg}'); location.href='/admin/members';</script>"
    return f"<script>alert('{msg}'); history.back();</script>"

##################### 게시판 #######################################################################
@app.route("/board/list")
def board_list():                            # 게시글 전체보기
    board_type = request.args.get("type", "notice")
    # ?type=notice/free/qna (기본 notice)

    keyword = (request.args.get("q") or "").strip()
    # ?q=검색어

    boards = BoardService.list(board_type=board_type, keyword=keyword)
    # DB에서 목록 가져오기

    return render_template("board_list.html",
                           boards=boards,
                           board_type=board_type,
                           keyword=keyword)

@app.route("/board/write", methods=["GET", "POST"])
def board_write():                          # 게시글 등록
    if "user_id" not in session:
        return "<script>alert('로그인이 필요합니다.');location.href='/login';</script>"

    if request.method == "GET":
        return render_template("board_write.html")

    title = (request.form.get("title") or "").strip()
    content = (request.form.get("content") or "").strip()
    board_type = request.form.get("board_type", "notice")
    is_pinned = 1 if request.form.get("is_pinned") == "on" else 0
    display_date = request.form.get("display_date") or None

    if not title or not content:
        return "<script>alert('제목과 내용을 입력하세요.');history.back();</script>"
    conn = Session.get_connection()
    try:
        with conn.cursor() as cursor:
            sql = """
                INSERT INTO boards
                (member_id, title, content, board_type, is_pinned, display_date)
                VALUES (%s,%s,%s,%s,%s,%s)
            """
            cursor.execute(sql, (
                session["user_id"],
                title,
                content,
                board_type,
                is_pinned,
                display_date
            ))
        conn.commit()
    finally:
        conn.close()
    return redirect(url_for("board_list"))

@app.route('/board/view/<int:board_id>')
def board_view(board_id):                   # 게시글 상세보기

    conn = Session.get_connection()
    try:
        with conn.cursor() as cursor:
            #조회수 +1 (먼저 증가)
            cursor.execute("""
                UPDATE boards
                SET view_count = view_count + 1
                WHERE id=%s
            """, (board_id,))
            conn.commit()
            #게시글 + 작성자 조회
            cursor.execute("""
                SELECT b.*, m.name, m.uid
                FROM boards b
                JOIN members m ON b.member_id = m.id
                WHERE b.id=%s
            """, (board_id,))
            board = cursor.fetchone()
            if not board:
                return "<script>alert('존재하지 않는 글');history.back();</script>"

            #댓글 + 작성자
            cursor.execute("""
                SELECT c.*, m.name, m.uid
                FROM board_comments c
                JOIN members m ON c.member_id = m.id
                WHERE c.board_id=%s
                ORDER BY COALESCE(c.parent_id, c.id), c.id
            """, (board_id,))
            comments = cursor.fetchall()

        return render_template(
            'board_view.html',
            board=board,
            comments=comments
        )
    finally:
        conn.close()

@app.post("/board/comment/add")
def board_comment_add():
    if "user_id" not in session:
        return "<script>alert('로그인이 필요합니다.');history.back();</script>"

    board_id_raw = request.form.get("board_id")
    if not board_id_raw or not board_id_raw.isdigit():
        return "<script>alert('잘못된 요청입니다.');history.back();</script>"

    board_id = int(board_id_raw)
    content = (request.form.get("content") or "").strip()
    parent_id = (request.form.get("parent_id") or "").strip()

    if not content:
        return "<script>alert('댓글 내용을 입력하세요.');history.back();</script>"

    parent_id = int(parent_id) if parent_id.isdigit() else None

    conn = Session.get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO board_comments(board_id, member_id, content, parent_id)
                VALUES (%s, %s, %s, %s)
            """, (board_id, session["user_id"], content, parent_id))
        conn.commit()
    finally:
        conn.close()

    return redirect(f"/board/view/{board_id}")


@app.post("/board/like/toggle")
def board_like_toggle():
    if "user_id" not in session:
        return jsonify({"ok": False, "msg": "login_required"}), 401

    data = request.get_json(silent=True) or {}
    board_id_raw = data.get("board_id")

    if not board_id_raw or not str(board_id_raw).isdigit():
        return jsonify({"ok": False, "msg": "invalid_board_id"}), 400

    board_id = int(board_id_raw)
    member_id = session["user_id"]

    conn = Session.get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT id FROM board_likes
                WHERE board_id=%s AND member_id=%s
            """, (board_id, member_id))
            row = cursor.fetchone()

            if row:
                cursor.execute("DELETE FROM board_likes WHERE id=%s", (row["id"],))
                liked = False
            else:
                cursor.execute("""
                    INSERT INTO board_likes(board_id, member_id)
                    VALUES (%s,%s)
                """, (board_id, member_id))
                liked = True

            cursor.execute("SELECT COUNT(*) AS cnt FROM board_likes WHERE board_id=%s", (board_id,))
            cnt = cursor.fetchone()["cnt"]

        conn.commit()
        return jsonify({"ok": True, "liked": liked, "count": cnt})
    finally:
        conn.close()



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
