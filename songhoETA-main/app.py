from flask import Flask, request, jsonify, render_template
import json
import os
import traceback
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

USER_FILE = 'users.json'
SECURITY_CODE_FILE = 'security_codes.json'
ADMIN_PASSWORD = "1234"

# JSON 저장 함수 (한글 깨짐 방지용)
def save_json(filename, data):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# JSON 불러오기 함수
def load_json(filename):
    if not os.path.exists(filename):
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump({}, f, ensure_ascii=False)
    with open(filename, 'r', encoding='utf-8') as f:
        return json.load(f)

def check_admin(password):
    return password == ADMIN_PASSWORD

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/check_id', methods=['POST'])
def check_id():
    data = request.get_json()
    user_id = data.get('id', '').strip()

    users = load_json(USER_FILE)
    security_codes = load_json(SECURITY_CODE_FILE)

    if not user_id:
        return jsonify(success=False, message="ID를 입력해주세요.")
    if user_id in users:
        return jsonify(success=False, message="이미 존재하는 ID입니다.")
    if user_id not in security_codes:
        return jsonify(success=False, message="등록되지 않은 ID입니다.")
    return jsonify(success=True, message="사용 가능한 ID입니다.")

@app.route('/api/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        user_id = data.get('id', '').strip()
        password = data.get('password', '')
        security_code_input = data.get('security_code', '').strip()

        users = load_json(USER_FILE)
        security_codes = load_json(SECURITY_CODE_FILE)

        if not user_id or not password or not security_code_input:
            return jsonify(success=False, message="모든 항목을 입력해주세요.")
        if user_id not in security_codes:
            return jsonify(success=False, message="등록되지 않은 ID입니다.")
        if security_code_input != security_codes[user_id]:
            return jsonify(success=False, message="보안코드가 올바르지 않습니다.")
        if user_id in users and users[user_id] != "":
            return jsonify(success=False, message="이미 가입된 ID입니다.")

        user = users.get(user_id)  #추가- user 변수
        
        #role 추가
        users[user_id] = {
            "pw_hash":pw_hash,
            "role":"user"
            }
        save_json(USER_FILE, users)

        return jsonify(success=True, message="회원가입 성공")

    except Exception as e:
        traceback.print_exc()
        return jsonify(success=False, message="서버 오류: " + str(e))

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    user_id = data.get('id', '').strip()
    password = data.get('password', '')

    users = load_json(USER_FILE)
    user = users.get(user_id)
    pw_hash = users.get(user_id, '')

    if not user or not check_password_hash(user.get('pw_hash', ''), password):
        return jsonify(success=False, message="ID 또는 비밀번호가 올바르지 않습니다.")
    
    #추가 - role 가져오기
    role = user.get('role', 'user')
    return jsonify(success=True, message=f"{user_id}님 환영합니다!", role=role)

#추가 - 관리자 계정으로 사용자 목록 받아오기
@app.route('/api/get_users', methods=['POST'])  
def get_users():
    data = request.get_json()
    user_id = data.get('id', '')

    users = load_json(USER_FILE)
    user = users.get(user_id, {})
    if user.get("role") != "admin":
        return jsonify(success=False, message="접근 권한이 없습니다.")

    user_list = [{"id": uid} for uid, info in users.items() if info.get("role") == "user"]
    return jsonify(success=True, users=user_list)


@app.route('/api/admin_login', methods=['POST'])
def admin_login():
    data = request.get_json()
    admin_pw = data.get('password', '')
    if admin_pw == ADMIN_PASSWORD:
        users = load_json(USER_FILE)
        user_list = [{"id": uid} for uid in users if users[uid] != ""]
        return jsonify(success=True, users=user_list)
    else:
        return jsonify(success=False, message="관리자 비밀번호가 올바르지 않습니다.")

@app.route('/api/delete_user', methods=['POST'])
def delete_user():
    data = request.get_json()
    user_id = data.get('id', '')

    users = load_json(USER_FILE)
    if user_id in users:
        del users[user_id]
        save_json(USER_FILE, users)
        return jsonify(success=True)
    else:
        return jsonify(success=False, message="해당 사용자를 찾을 수 없습니다.")

# 관리자 인증 필요: 보안코드 추가 API
@app.route('/api/add_security_code', methods=['POST'])
def add_security_code():
    data = request.get_json()
    admin_pw = data.get('admin_password', '')
    if not check_admin(admin_pw):
        return jsonify(success=False, message="관리자 인증 실패")

    student_id = data.get('id', '').strip()
    code = data.get('code', '').strip()

    if not student_id or not code:
        return jsonify(success=False, message="ID와 보안코드를 모두 입력해주세요.")

    security_codes = load_json(SECURITY_CODE_FILE)
    if student_id in security_codes:
        return jsonify(success=False, message="이미 존재하는 학생 ID입니다.")

    security_codes[student_id] = code
    save_json(SECURITY_CODE_FILE, security_codes)
    return jsonify(success=True, message="학생 추가 완료")

# 관리자 인증 필요: 보안코드 삭제 API
@app.route('/api/delete_security_code', methods=['POST'])
def delete_security_code():
    data = request.get_json()
    admin_pw = data.get('admin_password', '')
    if not check_admin(admin_pw):
        return jsonify(success=False, message="관리자 인증 실패")

    student_id = data.get('id', '').strip()

    security_codes = load_json(SECURITY_CODE_FILE)
    if student_id not in security_codes:
        return jsonify(success=False, message="존재하지 않는 학생 ID입니다.")

    del security_codes[student_id]
    save_json(SECURITY_CODE_FILE, security_codes)
    return jsonify(success=True, message="학생 삭제 완료")

if __name__ == '__main__':
    users = load_json(USER_FILE)
     #추가 - 관리자 계정 자동 추가되도록
    if "admin" not in users: 
        users["admin"] = {
            "pw_hash": generate_password_hash("admin1234"),  #초기 관리자 비번
            "role": "admin"
        }
        save_json(USER_FILE, users)

    security_codes = load_json(SECURITY_CODE_FILE)
    defaults = {
        "10101홍길동": "QWERTY",
        "10202김철수": "ASDFGH",
    }
    updated = False
    for k, v in defaults.items():
        if k not in security_codes:
            security_codes[k] = v
            updated = True
    if updated:
        save_json(SECURITY_CODE_FILE, security_codes)

    app.run(debug=True)
