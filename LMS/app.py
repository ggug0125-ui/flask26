# pip install flask
# 플라스크란?
# 파이썬으로 만든 db연동 콘솔 프로그램을 웹으로 연결하는 프레임워크임
# 프레임워크 : 미리 만들어 놓은 틀 안에서 작업하는 공간
# app.py 는 플라스크로 서버를 동작하기 위한 파일명(기본파일)
# static, templates 폴더 필수 (프론트용 파일 모이는 곳)
# static : 정적파일을 모아 놓음 (html, css, js)
# templates : 동적파일을 모아 놓음 (crud 화면, 레이아웃, index 등....)
from flask import Flask, render_template, request, redirect, url_for, session
#                플라스크      프론트연결     요청,응답    주소전달    주소생성   상태저장소
#             app.route를연결                 .get등
from LMS.common import Session
from LMS.domain import Board

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'
# 세션을 사용하기 위해 보안키 설정 (아무 문자열이나 입력)
# RuntimeError: The session is unavailable because no secret key was set.
# Set the secret_key on the application to something unique and secret.

@app.route('/login', methods=['GET','POST']) # http://localhost:5000/login
    # methods는 웹에 동작을 관여한다.
    # GET : URL 주소로 데이터를 처리(보안상 좋지 않음, 빠름)
    # POST : BODY영역에서 데이터를 철리(보안상 좋음, 대용량에서 많이 사용함)
    # 대부분 처음에 화면(HTML렌더)을 요청할 때는 GET 방식으로 처리
    # 화면에 있는 내용을 백엔드로 전달할 때는 POST 방식으로 처리
def login():
    if request.method == 'GET': # 처음접속하면 GET방식으로 화면 출력용
        return render_template('login.html')
        # get방식으로 요청하면 login.html 화면이 나옴

    # login.html에서 action="/login" method="POST"처리용 코드
    # login.html에서 넘어온 폼 데이터는 uid / upw
    uid = request.form.get('uid') # 요청한  폼내용을 가져옴
    upw = request.form.get('upw') # request  form  get
    # print("/login에서 넘어온 폼 데이터 출력 테스트 ")
    # print(uid, upw)
    # print("===================================")

    conn = Session.get_connection() # 교사용 db에 접속용 객체
    try: # 예외발생 가능성 있음
        with conn.cursor() as cursor: # db에 커서객체 사용
            # 1회원 정보 조회
            sql = "SELECT id, name, uid, role  \
            FROM members WHERE uid = %s AND password = %s"
            #                  uid가 동일 &  pwd가 동일
            #    id, name, uid, role 가져온다.
            cursor.execute(sql, (uid, upw)) # 쿼리문 실행
            user = cursor.fetchone() # 쿼리 결과 1개를 가져와 user 변수에 넣음

            if user:
                # 찾은 계정이 있으면 브라우져의 세션영역에 보관한다.
                session['user_id'] = user['id'] # 계정일련번호(회원번호)
                session['user_name'] = user['name'] # 계정이름
                session['user_uid'] = user['uid']  # 계정로그인명
                session['user_role'] = user['role']  # 계정권한
                # 세션에 저장 완료
                # 브라우저에서 f12번 누르고 애플리케이션 탭에서 쿠키 항복에 가면 session객체가 보임
                # 이것을 삭제하면 로그아웃 처리 됨
                return redirect(url_for('index'))
                # 처리후 이동하는 경로 http://localhost:/index로 감(get 메서드 방식)
            else :
                # 찾은 계정이 없다.
                return "<script>alert('아이디나 비번이 틀렸습니다.');history.back();</script>"
            #                  경고창발생                          뒤로가기
    finally:
        conn.close() # db 연결 종료


@app.route('/logout') # 기본동작이 get방식이라 , methods=['GET'] 생략가능
def logout():
    session.clear()  # 세션 비우기
    return redirect(url_for('login'))# http://localhost:5000/login (get방식)

@app.route('/join', methods=['GET','POST']) # 회원가입용 함수
def join(): # http://localhost:5000/ get메서드(화면출력) post(화면폼처리용)
    if request.method == 'GET':
        return render_template('join.html') # 로그인화면용 프론트로 보냄

    # POST 메서드 인 경우 (폼으로 데이터가 넘어올때 처리)

    uid = request.form.get('uid')
    password = request.form.get('password')
    name = request.form.get('name') # 폼에서 넘어온 값을 변수에 넣음

    conn = Session.get_connection() # db에 연결
    try: # 예외발생 가능성이 있는 코드
        with conn.cursor() as cursor:
            # 아이디 중복 확인
            cursor.execute("SELECT id FROM members WHERE uid = %s", (uid,))
            if cursor.fetchone():
                return "<script>alert('이미 존재하는 아이디입니다.'); history.back();</script>"

            # 회원 정보 저장 (role, active는 기본값이 들어감)
            sql = "INSERT INTO members (uid, password, name) VALUES (%s, %s, %s)"
            cursor.execute(sql, (uid, password, name))
            conn.commit()

            return "<script>alert('회원가입이 완료되었습니다!'); location.href='/login';</script>"
    except Exception as e: # 예외발생시 실행문
        print(f"회원가입 에러: {e}")
        return "가입 중 오류가 발생했습니다. /n join()메서드를 확인하세요!!!"

    finally:   # 항상 실행문
        conn.close()

@app.route('/member/edit', methods=['GET', 'POST'])
def member_edit():
    if 'user_id' not in session: # 셔센에 user_id가 없으면
        return redirect(url_for('login'))  # 로그인 경로로 보냄

    # 있으면 db연결 시작!
    conn = Session.get_connection()
    try :
        with conn.cursor() as cursor:
            if request.method == 'GET':
                # 기존 정보 불러오기
                cursor.execute("SELECT * FROM members WHERE id = %s", (session['user_id'],))
                user_info = cursor.fetchone()
                return render_template('member_edit.html', user=user_info)
                #                     가장 중요한 포인트    get요청시 페이지     객체 전달용 코드

            # POST 요청: 정보 업데이트
            new_name = request.form.get('name')
            new_pw = request.form.get('password')

            if new_pw:  # 비밀번호 입력 시에만 변경
                sql = "UPDATE members SET name = %s, password = %s WHERE id = %s"
                cursor.execute(sql, (new_name, new_pw, session['user_id']))
            else:  # 이름만 변경
                sql = "UPDATE members SET name = %s WHERE id = %s"
                cursor.execute(sql, (new_name, session['user_id']))

            conn.commit()
            session['user_name'] = new_name  # 세션 이름 정보도 갱신
            return "<script>alert('정보가 수정되었습니다.'); location.href='/mypage';</script>"

    except Exception as e:# 예외발생시 실행문
        print(f"회원수정 에러: {e}")
        return "수정 중 오류가 발생했습니다. /n member_edit()메서드를 확인하세요!!!"

    finally:  # 항상 실행문
        conn.close()


@app.route('/mypage') ## http://localhost:5000/mypage (get방식)
def mypage():
    if 'user_id' not in session: # 로그인 상태확인
          return redirect(url_for('login'))  # 로그인이 아니면 http://localhost:5000/login으로 보냄
    #            그냥 호출할때
    conn = Session.get_connection() # db연결

    try:
        with conn.cursor() as cursor:
            # 1. 내 상세 정보 조회
            cursor.execute("SELECT * FROM members WHERE id = %s", (session['user_id'],))
            # 로그인한 정보를 가지고 디비에서 찾아옴
            user_info = cursor.fetchone() # 찾아온값 1개를 user_info에 담음(딕셔너리타입)

            # 2. 내가 쓴 게시글 개수 조회 (작성하신 boards 테이블 활용)
            cursor.execute("SELECT count(*) as board_count from boards where member_id = %s", (session['user_id'],))
            #                      갯수    보드카운드                           내가쓴 아이디
            #                                                   보드테이블에 있는 멤버아이디의 값을 가져옴
            #                      갯수를 세어 fetchone()에 넣는다 -> board_count이름으로 개수를 가지고있음
            board_count = cursor.fetchone()['board_count']

            return render_template('mypage.html', user=user_info, board_count=board_count)
            # 결과를 리턴한다                         mypage.html 에게 user객체와 board_count객체를 담아 보낸다.
            # 프론트에서 사용하려면 {{user.???}} {{board_count}}이런식으로 써먹으면된다.

    finally:
        conn.close()
#####################################  여기까지 회원 CRUD ################################################

#########################################  게시판 CRUD ##################################################

@app.route('/board/write', methods=['GET', 'POST']) ## http://localhost:5000/write
def board_write():
    if request.method == 'GET':
        # 로그인 체크 (로그인 안했으면 글 못쓰게)
       if 'user_id' not in session:
           return '<script>alert("로그인 후 이용 가능합니다.");location.href="/login";</script>'
       return render_template('board_write.html')
        #     값이있을때 호출하는것

       # 2 사용자가 '등록하기'버튼을 눌러서 테이터를 보냈을 때 (디비저장)
    elif request.method == 'POST': # board_write.html 파일에 <form action="/board/write" method="POST">이게 넘어왔을때
        title = request.form.get('title')
        content = request.form.get('content')
        # 세션에 저장된 로그인 유저의 id (member_id)
        member_id = session.get('user_id')

        conn = Session.get_connection()
        try:
            with conn.cursor() as cursor:
                sql = "INSERT INTO boards (member_id, title, content) VALUES (%s, %s, %s)"
                cursor.execute(sql, (member_id, title, content))
                conn.commit()
            return redirect(url_for('board_list'))   #저장후 목록으로 이동
                #   값이 없이 호출할때 get으로 그냥 호출할때
        except Exception as e:
            print(f"글쓰기 에러 : {e}")
            return "저장 중 에러가 발생했습니다."
        finally:
            conn.close()

@app.route('/board') ## http://localhost:5000/board
def board_list():
    conn = Session.get_connection()
    try:
        with conn.cursor() as cursor:
            #작성자 이름을 함께 가져오기 위해 join사용
            sql = """
                select b.*, m.name as writer_name
                from boards b
                join members m on b.member_id = m.id
                order by b.id desc
            """
            cursor.execute(sql)
            rows = cursor.fetchall()
            boards = [Board.from_db(row) for row in rows] # from LMS.domain import Board
            return render_template('board_list.html', boards=boards)
            #      객체보낼때
    finally:
        conn.close()

@app.route('/board/view/<int:board_id>') # http://localhost:5000/board/view/99(게시물번호)
def board_view(board_id):
    conn = Session.get_connection()
    try:
        with conn.cursor() as cursor:
            #join을 통해 작성자 정보(name,uid)를 함께 조회
            sql = """
            select b.*, m.name as writer_name, m.uid as writer_uid
            from boards b
            join members m on b.member_id = m.id
            where b.id = %s
        """
            # boards는 b라는 이름으로 다가져와 조인으로 멤버와 멤버아이디를 조인
            # 이문이 중요~!! 이해하자~!! gpt에 물어바 자세히알아보기

            cursor.execute(sql, (board_id,))
            row = cursor.fetchone()
        print(row) #db에서 나온 딕셔너리타입 콘솔에 출력 테스트용
        if not row:
            return "<script>alert('존재하지 않는 게시글입니다.'); history.back();</script>"

        #board 객체로 변환 (앞서 작성한 board.py의 from_db 활용)
        board = Board.from_db(row)

        return render_template('board_view.html', board=board)
    finally:
        conn.close()

@app.route('/board/edit/<int:board_id>',methods=['GET','POST'])
def board_edit(board_id):
    conn = Session.get_connection()
    try:
        with conn.cursor() as cursor:
            if request.method == 'GET':
                sql = "select * from boards where id =%s"
                cursor.execute(sql,(board_id,))
                row = cursor.fetchone()

                if not row:
                    return "<script>alert('존재하지 않는 게시글입니다.'); history.back();</script>"

                if row['member_id'] != session['user_id']:
                    return "<script>alert('수정 권한이 없습니다.'); history.back();</script>"
                print(row)
                board = Board.from_db(row)
                return render_template('board_edit.html', board=board)

            elif request.method == 'POST':
                title = request.form.get('title')
                content = request.form.get('content')

                sql = "UPDATE boards SET title = %s, content = %s WHERE id = %s"
                cursor.execute(sql, (title, content, board_id))
                conn.commit()

                return redirect(url_for('board_view',board_id=board_id))
    finally:
        conn.close()

@app.route('/board/delete/<int:board_id>')
def board_delete(board_id):
    # 세션에 있는 아이디와 작성자가 같으면 삭제 가능하게 코드짜놓기~!!
    conn = Session.get_connection()
    try:
        with conn.cursor() as cursor:
            sql = "DELETE FROM boards WHERE id = %s"
            cursor.execute(sql, (board_id,))
            conn.commit()

            if cursor.rowcount == 0:
                print(f"게시글{board_id}번 삭제 성공")
            else:
                return "<script>alert('삭제할 게시글이 없거나 권한이 없습니다.)'); history.back();</script>"
        return redirect(url_for('board_list'))
    except Exception as e:
        print(f"삭제 에러: {e}")
        return "삭제 중 오류가 발생했습니다."
    finally:
        conn.close()



######################################### 게시판 CRUD  END ##############################################
@app.route('/') # url 생성용 코드 http://localhost:5000/ or http://192.168.0.???:5000
def index():
    return render_template('main.html')
    # render_template 웹브라우저로 보낼 파일명
    # templates 라는 폴더에서 main.html을 찾아 보냄

if __name__ == '__main__':

    app.run(host='0.0.0.0', port=5000, debug=True)
    # host='0.0.0.0' 누가요청하던 응답해라
    # port=5000 플라스크에서 사용하는 포트번호
    # debug=True 콘솔에서 디버그를 보겠다.
