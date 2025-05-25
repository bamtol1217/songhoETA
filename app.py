from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'  # SQLite DB 파일
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# 사용자 모델 (DB 테이블)
class User(db.Model):
    id = db.Column(db.String(50), primary_key=True)  # 학번+이름
    password_hash = db.Column(db.String(128), nullable=False)

# 보안코드 모델 (DB 테이블)
class SecurityCode(db.Model):
    id = db.Column(db.String(50), primary_key=True)  # 학번+이름
    code = db.Column(db.String(50), nullable=False)

# 관리자 비밀번호 (간단하게 하드코딩)
ADMIN_PASSWORD = "1234"

# 미리 할당된 보안코드 데이터 (예시)
preassigned_codes = {
    "10101홍길동": "QWERTY",
    "10202김철수": "ASDFGH",
    # ... 실제 천명 이상이라면 DB나 파일로 관리
}

@app.route('/')
def index():
    return render_template('index.html')  # HTML 템플릿

@app.route('/api/check_id', methods=['POST'])
def check_id():
    data = request.get_json()
    user_id = data.get('id', '').strip()

    if not user_id:
        return jsonify(success=False, message="ID를 입력해주세요.")
    if User.query.filter_by(id=user_id).first():
        return jsonify(success=False, message="이미 존재하는 ID입니다.")
    if not SecurityCode.query.get(user_id):
        return jsonify(success=False, message="등록되지 않은 ID입니다.")
    return jsonify(success=True, message="사용 가능한 ID입니다.")

@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    user_id = data.get('id', '').strip()
    password = data.get('password', '')
    security_code_input = data.get('security_code', '').strip()

    # 보안코드 DB 조회
    sc = SecurityCode.query.get(user_id)
    if not sc:
        return jsonify(success=False, message="등록되지 않은 ID입니다.")
    if security_code_input != sc.code:
        return jsonify(success=False, message="보안코드가 올바르지 않습니다.")

    existing_user = User.query.get(user_id)
    if existing_user and existing_user.password_hash != "":
        return jsonify(success=False, message="이미 가입된 ID입니다.")

    pw_hash = generate_password_hash(password)

    if existing_user:
        existing_user.password_hash = pw_hash
    else:
        user = User(id=user_id, password_hash=pw_hash)
        db.session.add(user)

    db.session.commit()
    return jsonify(success=True, message="회원가입 성공")

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    user_id = data.get('id', '').strip()
    password = data.get('password', '')

    user = User.query.get(user_id)
    if not user or user.password_hash == "":
        return jsonify(success=False, message="ID 또는 비밀번호가 올바르지 않습니다.")
    if check_password_hash(user.password_hash, password):
        return jsonify(success=True, message=f"{user_id}님 환영합니다!")
    else:
        return jsonify(success=False, message="ID 또는 비밀번호가 올바르지 않습니다.")

@app.route('/api/admin_login', methods=['POST'])
def admin_login():
    data = request.get_json()
    admin_pw = data.get('password', '')
    if admin_pw == ADMIN_PASSWORD:
        users = User.query.filter(User.password_hash != "").all()  # 가입된 회원만
        user_list = [{"id": u.id} for u in users]
        return jsonify(success=True, users=user_list)
    else:
        return jsonify(success=False, message="관리자 비밀번호가 올바르지 않습니다.")

@app.route('/api/delete_user', methods=['POST'])
def delete_user():
    data = request.get_json()
    user_id = data.get('id', '')
    user = User.query.get(user_id)
    if user:
        db.session.delete(user)
        db.session.commit()
        return jsonify(success=True)
    else:
        return jsonify(success=False, message="해당 사용자를 찾을 수 없습니다.")

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        # 보안코드 테이블에 미리 할당된 보안코드 등록
        for sid, code in preassigned_codes.items():
            if not SecurityCode.query.get(sid):
                sc = SecurityCode(id=sid, code=code)
                db.session.add(sc)
        db.session.commit()

    app.run(debug=True)
