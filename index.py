#!/var/www/new/Flask
# -*- coding: utf-8 -*-
import sqlite3
import datetime
import time
import sys
import webbrowser
import os.path
from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash, escape
from flask_login import LoginManager, UserMixin, login_required, login_user, logout_user, current_user
# Python 2.x 버전에서 작동하는 Application입니다.

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = "./LibraryDB.db" #LINUX

# Flask application 생성
app = Flask(__name__)
app.config.from_object(__name__)
app.secret_key = b"c2hmcnlqIGRzZmhzZGg1eWRmIApkZg=="

reload(sys)
sys.setdefaultencoding('utf-8')

# Login 관리
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# Backend Settings

@login_manager.user_loader
def load_user(user_id):
    # LoginManager 용 함수
    # 입력 : 불러오고자 하는 유저의 ID (userID)
    # 리턴 : 해당 ID를 가진 유저
    cur = g.db.cursor()
    cur.execute("SELECT userid, userpw FROM users WHERE userid=(?)", [user_id])
    loggedin = cur.fetchone()
    if loggedin is None:
        print("No user detected")
        return None
    else:
        user = User(loggedin[0], loggedin[1])
        print(user)
        return user



class User(UserMixin):
    # 사용자 오브젝트
    # 사용자 계정 정보 (아이디, 패스워드, 인증여부, 접속여부, 익명여부) 보관 등
    user_id = u""
    userPW = u""
    authenticated = False
    active = True
    anonymous = False


    def __init__(self, userID, userPW, auth = False):
        #super(User, self).__init__()
        self.user_id = userID
        self.userPW = userPW
        self.authenticated = auth
        self.active = True
        self.anonymous = False

    def __repr__(self):
        return "[User %s]" % self.user_id


    def is_authenticated(self):
        return self.authenticated

    def is_active(self):
        return self.active

    def is_anonymous(self):
        return self.anonymous

    def get_id(self):
        return self.user_id

def getUser():
    if session.get('logFlag') == False:
        return url_for("login")
    user_id = session['userID']
    return user_id

# 데이터베이스 설정
def dbconn():
    return sqlite3.connect(app.config['DATABASE'])

@app.before_request
def before_request():
    g.db = dbconn()

@app.teardown_request
def teardown_request(exception):
    g.db.close()



# =================== 기타 기능 ======================

# 현재시각
def clock():
    # 현재 시간 정보를 문자열로 return
    weekdays = {"Sun" : u"일요일", "Mon" : u"월요일", "Tue" : u"화요일", "Wed" : u"수요일", "Thu" : u"목요일", "Fri" : u"금요일", "Sat" : u"토요일"}

    now = datetime.datetime.now()
    year = datetime.datetime.strftime(now, "%Y")
    month = datetime.datetime.strftime(now, "%m")
    day = datetime.datetime.strftime(now, "%d")
    hour = datetime.datetime.strftime(now, "%I")
    minute = datetime.datetime.strftime(now, "%M")
    sec = datetime.datetime.strftime(now, "%S")
    apm = datetime.datetime.strftime(now, "%p")
    weekday = weekdays[datetime.datetime.strftime(now, "%a")]

    timestr = u"%s년 %s월 %s일 (%s) %s:%s:%s %s" % (year, month, day, weekday, hour, minute, sec, apm)
    return timestr



# =================== 검색 기능 ======================

def search(q, itemtype):
    # 복수의 키워드 검색을 어절 단위로 나누어 검색하는 질의 제작
    # 모든 키워드가 포함된 경우 먼저 찾고 일부 포함된 경우를 다음으로 검색

    # 검색 입력 List화
    keywords = q.split(" ")
    cur = g.db.cursor()

    # 단일 키워드, 또는 공백일 때
    if len(keywords) == 1:
        cur.execute(u"SELECT * FROM docs WHERE itemtype='%s' AND title LIKE '%%%s%%'" % (itemtype, keywords[0]))
        return cur.fetchall()

    # AND 질의
    and_query = u"SELECT * FROM docs WHERE itemtype='%s' AND (title LIKE '%%%s%%'" % (itemtype, keywords[0])

    for key in keywords[1:]:
        new_query = " AND title LIKE '%%%s%%'" % key
        and_query += new_query

    and_query += ")"

    cur.execute(and_query)
    and_result = cur.fetchall()

    # OR 질의

    or_query = u"SELECT * FROM docs WHERE itemtype='%s' AND (title LIKE '%%%s%%'" % (itemtype, keywords[0])

    for key in keywords[1:]:
        new_query = " OR title LIKE '%%%s%%'" % key
        or_query += new_query

    or_query += ")"

    cur.execute(or_query)
    or_result = cur.fetchall()

    return and_result + or_result



# ======================== 웹 기능 =========================


# 시작 화면 - 로그인 페이지
@app.route("/")
def start():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return render_template("login.html")


@login_manager.unauthorized_handler
def unauthorized():
    # TODO: 추가 필요 작업
    return render_template("exit.html", msg=u"접근 권한을 가지고 있지 않습니다.")


# 로그인 시도
@app.route("/login", methods=["POST"])
def login():
    if request.method == "POST":
        # ID, PW
        userID = request.form["userID"]
        userPW = request.form["userPW"]

        if userID == "": # 아이디 입력 안 했을 때 오류
            return render_template("login.html", msg=u"아이디를 입력해 주십시오.")
        elif userPW == "": # 패스워드 입력 안 했을 때 오류
            return render_template("login.html", msg=u"패스워드를 입력해 주십시오.")
        else:
            cur = g.db.cursor()
            cur.execute("SELECT userid, userpw, name FROM users WHERE userid=(?) AND userpw=(?)", [userID, userPW])
            if len(cur.fetchall()) == 1:
                loggedin = cur.fetchone()
                user = User(userID, userPW)
                #print(user) # DEBUG: User 생성 확인
                login_user(user, remember=True)
                return redirect(url_for('main')) # 로그인 성공
            else: # ID, PW 틀렸을 때 오류
                return render_template("login.html", msg=u"존재하지 않거나 틀린 아이디 또는 패스워드를 입력하셨습니다.")

    else:
        return render_template("login.html", msg=u"잘못된 접근입니다.")
# 계정 생성
@app.route("/signup", methods=["POST", "GET"])
def signup():
    if request.method == "POST":
        userID = request.form['userID']
        userPW = request.form['userPW']
        PWconfirm = request.form['PWconfirm']
        username = request.form['username']
        if userID == "":
            return render_template("signup.html", msg=u"아이디를 입력해주세요.")
        elif userPW == "":
            return render_template("signup.html", msg=u"패스워드를 입력해주세요.")
        elif username == "":
            return render_template("signup.html", msg=u"이름을 입력해주세요.")
        elif PWconfirm == "" or userPW != PWconfirm:
            return render_template("signup.html", msg=u"패스워드를 확인해주세요.")
        else:
            cur = g.db.cursor()
            cur.execute("SELECT userid FROM users WHERE userid = (?)", [userID])
            if len(cur.fetchall()) >= 1:
                return render_template("signup.html", msg=u"이미 존재하는 아이디입니다.")
            else:
                cur.execute("INSERT INTO users (userid, userpw, name) VALUES (?,?,?)", [userID, userPW, username])
                g.db.commit()
                return render_template("login.html", msg=u"계정을 성공적으로 생성했습니다.")
    else:
        return render_template("signup.html")

# 계정 생성 시도

# 로그아웃
@app.route("/logout")
def logout():
    logout_user()
    msg = u"성공적으로 로그아웃 하셨습니다."
    session.pop('username', None)
    return render_template("login.html", msg=msg)



# 패스워드 찾기 1 : findacct.html
@app.route("/findacct", methods=["GET", "POST"])
def forgotpw():

    return render_template("findacct.html")

# 패스워드 찾기 2 : pwreset.html
@app.route("/forgotpw", methods=["GET", "POST"])
def pwreset():
    if request.method == "GET":
        return render_template("exit.html", msg=u"비정상적인 접근입니다.")
    if request.method == "POST":
        userID = request.form['userID']
        name = request.form['username']

        if userID == "":
            return render_template("findacct.html", msg=u"아이디를 입력해주세요.")
        elif name == "":
            return render_template("findacct.html", msg=u"이름을 입력해주세요.")
        else:
            cur = g.db.cursor()
            cur.execute("SELECT userID, name FROM users WHERE userID=(?) AND name=(?)", [userID, name])
            acct = cur.fetchall()
            if len(acct) == 1:
                return render_template("pwreset.html", userID=userID, name=name)
            else:
                return render_template("findacct.html", msg=u"입력하신 이름과 아이디를 가진 계정이 존재하지 않습니다.")
    return render_template("exit.html", msg=u"비정상적인 접근입니다.")

# 패스워드 찾기 3
@app.route("/resetpw", methods=["GET", "POST"])
def resetpw():
    if request.method == "GET":
        return render_template("exit.html", msg=u"비정상적인 접근입니다.")
    if request.method == "POST":
        userID = request.form['userID']
        name = request.form['username']
        newPW = request.form['newPW']
        PWconfirm = request.form['PWconfirm']
        if newPW == "":
            return render_template("pwreset.html", msg=u"새 패스워드를 입력해주세요.")
        elif newPW != PWconfirm or PWconfirm == "":
            return render_template("pwreset.html", msg=u"패스워드를 확인해주세요.")
        else:
            cur = g.db.cursor()
            cur.execute("SELECT userid, name FROM users WHERE userid=(?)", [userID])
            acct = cur.fetchall()
            if len(acct) == 1:
                cur.execute("UPDATE users SET userpw=(?) WHERE userid=(?)", [newPW, userID])
                g.db.commit()
                return render_template("login.html", msg=u"패스워드를 성공적으로 재설정했습니다.")
            else:
                return render_template("exit.html", msg=u"비정상적인 접근입니다.")

    return render_template("exit.html", msg=u"비정상적인 접근입니다.")


# ============== 이하 로그인 상태에서만 접근할 수 있음 =============
# 검색 창 : main.html
@app.route("/main", methods=["GET", "POST"])
@login_required
def main():
    userID = current_user.get_id()
    cur = g.db.cursor()
    cur.execute(u"SELECT name FROM users WHERE userID=(?)", [userID])
    session['username'] = cur.fetchone()[0]
    return render_template("main.html", name=session['username'], current_time=clock())




# 결과 창 : show.html
@app.route("/show", methods=["GET"])
@login_required
def show():
    itemtype = request.args.get("itemtype")
    keyword = request.args.get("keyword")
    page = request.args.get("page")

    if itemtype is None or keyword is None:
        return redirect(url_for("main"))

    result = search(keyword, itemtype)

    # TODO: 페이지당 최대 10개씩 표시, 여러 페이지 결과 조회
    if page is None:
        page = 1
    else:
        page = int(page)

    pages = 0

    if len(result) > 10: # 결과가 1페이지를 넘길 경우
        pages = (len(result) // 10) + 1

        # 결과 수가 10의 배수일 경우 빈 페이지 발생 방지
        if len(result) % 10 == 0:
            pages -= 1

        # 초기값
        first = 0
        last = 0

        if page > pages: # 마지막 페이지 다음을 찾고 있을 경우 : 마지막 페이지 결과
            page = pages
            first = (page - 1) * 10
            last = len(result) + 1
        elif page < 1: # 첫 페이지 이전을 찾고 있을 경우 : 첫 페이지 결과
            page = 1
            first = 0
            last = 10
        else: # 정상 페이지 번호일 경우 그 페이지 표시
            first = (page - 1) * 10
            last = min(first + 10, len(result) + 1)

        result = result[first:last]
        return render_template("show.html", name=session['username'], itemtype=itemtype, keyword=keyword, page=page, pages=pages, result=result, current_time=clock())


    else: # 결과 10개 이하일 경우
        return render_template("show.html", name=session['username'], itemtype=itemtype, keyword=keyword, page=page, pages=1, result=result, current_time=clock())

# 자료 추가: add.html
@app.route("/add", methods=["GET", "POST"])
@login_required
def add():
    if request.method == "POST":
        itemtype = request.form['itemtype']
        title = request.form['title']
        category1 = request.form['category1']
        category2 = request.form['category2']
        location = request.form['location']
        source = u""
        created = u""
        if title == "":
            return render_template("add.html", name=session['username'], msg=u"제목을 입력해야 합니다.")
        if category1 == "":
            return render_template("add.html", name=session['username'], msg=u"대분류를 입력해야 합니다.")
        if itemtype is None:
            return render_template("add.html", name=session['username'], msg=u"종류를 선택하지 않았습니다.")
        if location == "":
            return render_template("add.html", name=session['username'], msg=u"위치를 입력해야 합니다.")

        if itemtype == "cd":
            created = request.form['varfield']
        else:
            source = request.form['varfield']


        cur = g.db.cursor()
        query = "INSERT INTO docs (itemtype, title, category1, category2, location, source, created) VALUES (?,?,?,?,?,?,?)"
        cur.execute(query, [itemtype, title, category1, category2, location, source, created])
        g.db.commit()
        return render_template("main.html", name=session['username'], msg=u"자료를 성공적으로 추가했습니다.", current_time=clock())
    else:
        return render_template("add.html", name=session['username'], current_time=clock())




# 자료 수정: edit.html
@app.route("/edit", methods=["GET", "POST"])
@login_required
def edit():
    if request.method == "GET":
        docid = request.args.get("id")
        cur = g.db.cursor()
        cur.execute("SELECT * FROM docs WHERE id = (?)", [docid])
        res = cur.fetchall()

        # 존재하지 않는 자료 요청 오류
        if len(res) == 0:
            return render_template("main.html", name=session['username'], current_time=clock(), msg=u"존재하지 않는 자료입니다.")

        doc = res[0]
        var = u""
        if doc[0] == "cd":
            var = doc[6]
        else:
            var = doc[5]
        return render_template("edit.html", docid=docid, itemtype=doc[0], title=doc[1], category1=doc[2], category2=doc[3], location=doc[4], var=var,  name=session['username'], current_time=clock())
    elif request.method == "POST":
        docid = request.form['bcid']
        itemtype = request.form['itemtype']
        title = request.form['title']
        category1 = request.form['category1']
        category2 = request.form['category2']
        location = request.form['location']
        varfield = request.form['varfield']
        source = u""
        created = u""

        if itemtype == "cd":
            created = varfield
        else:
            source = varfield

        query = "UPDATE docs SET itemtype=(?), title=(?), category1=(?), category2=(?), location=(?), source=(?), created=(?) WHERE id=(?)"

        if title == "":
            return render_template("edit.html", msg=u"제목을 입력해야 합니다.")
        if category1 == "":
            return render_template("edit.html", msg=u"대분류를 입력해야 합니다.")
        if location == "":
            return render_template("edit.html", msg=u"위치를 입력해야 합니다.")

        cur = g.db.cursor()
        cur.execute(query, [itemtype, title, category1, category2, location, source, created, docid])
        g.db.commit()
        return render_template("main.html", name=session['username'], current_time=clock(), msg=u"자료 정보를 성공적으로 수정했습니다.")

    else:
        return render_template("main.html", name=session['username'], current_time=clock(), msg=u"비정상적인 접근입니다.")



# 자료 삭제: delete.html
@app.route("/delete", methods=["POST", "GET"])
@login_required
def delete():
    query = u"DELETE FROM docs WHERE id = (?)"
    if request.method == "GET":
        docid = request.args.get("id")
        cur = g.db.cursor()
        cur.execute(query, [docid])
        g.db.commit()
        return render_template("main.html", name=session['username'], current_time=clock(), msg=u"자료를 성공적으로 삭제했습니다.")

    return render_template("main.html", name=session['username'], current_time=clock())


# 프로그램 실행
if __name__ == '__main__':
    # 사용 포트: 5700 (필요에 따라 추후 변경)
    # 현행 서버 IP: ***.***.***.*** (0.0.0.0 (default) 설정으로 IP 변경시에도 접속 가능)
    app.run(host="0.0.0.0", port=5700, threaded=True)
