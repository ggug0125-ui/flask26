from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from LMS.service import MemberService

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



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
