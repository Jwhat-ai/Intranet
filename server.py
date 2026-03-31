import os
import json
import zipfile
import io
import hashlib
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_file, send_from_directory
from werkzeug.utils import secure_filename
from docx import Document
import PyPDF2

# 导入知识库模块
from knowledge_base import search_knowledge_base, update_knowledge_base

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOADS_DIR = os.path.join(BASE_DIR, 'uploads')
DATA_DIR = os.path.join(BASE_DIR, 'data')
PROJECTS_FILE = os.path.join(DATA_DIR, 'projects.json')
ANNOUNCEMENTS_FILE = os.path.join(DATA_DIR, 'announcements.json')

ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'xls', 'xlsx', 'png', 'jpg', 'jpeg', 'gif', 'txt'}

os.makedirs(UPLOADS_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

if not os.path.exists(PROJECTS_FILE):
    with open(PROJECTS_FILE, 'w', encoding='utf-8') as f:
        json.dump([], f)

if not os.path.exists(ANNOUNCEMENTS_FILE):
    with open(ANNOUNCEMENTS_FILE, 'w', encoding='utf-8') as f:
        json.dump([{
            'id': 1,
            'content': '欢迎使用公司内部门户系统！',
            'priority': 'high',
            'date': datetime.now().isoformat()
        }], f, ensure_ascii=False, indent=2)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def read_json(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return []

def write_json(filepath, data):
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(hashed_password, password):
    return hashlib.sha256(password.encode()).hexdigest() == hashed_password

# 密码存储文件
PASSWORD_FILE = os.path.join(DATA_DIR, 'file_passwords.json')

if not os.path.exists(PASSWORD_FILE):
    write_json(PASSWORD_FILE, {})

# 管理员密码（可以在生产环境中改为从环境变量或配置文件读取）
ADMIN_PASSWORD = 'admin123'  # 默认管理员密码

@app.route('/api/admin/verify', methods=['POST'])
def verify_admin():
    data = request.get_json()
    password = data.get('password')
    
    if password == ADMIN_PASSWORD:
        return jsonify({'success': True})
    return jsonify({'success': False}), 401

def extract_text_from_file(filepath):
    ext = os.path.splitext(filepath)[1].lower()
    try:
        if ext == '.txt':
            with open(filepath, 'r', encoding='utf-8') as f:
                return f.read()
        elif ext == '.pdf':
            text = ''
            with open(filepath, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    text += page.extract_text() or ''
            return text
        elif ext == '.docx':
            doc = Document(filepath)
            return '\n'.join([para.text for para in doc.paragraphs])
    except Exception as e:
        print(f"Error extracting text: {e}")
    return ''

@app.route('/')
def index():
    return send_from_directory('public', 'index.html')

@app.route('/project.html')
def project_page():
    return send_from_directory('public', 'project.html')

@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory('public', filename)

@app.route('/api/announcements', methods=['GET'])
def get_announcements():
    return jsonify(read_json(ANNOUNCEMENTS_FILE))

@app.route('/api/announcements', methods=['POST'])
def add_announcement():
    data = request.get_json()
    announcements = read_json(ANNOUNCEMENTS_FILE)
    new_announcement = {
        'id': int(datetime.now().timestamp() * 1000),
        'content': data.get('content', ''),
        'priority': data.get('priority', 'normal'),
        'date': datetime.now().isoformat()
    }
    announcements.insert(0, new_announcement)
    write_json(ANNOUNCEMENTS_FILE, announcements)
    return jsonify(new_announcement)

@app.route('/api/announcements/<int:id>', methods=['DELETE'])
def delete_announcement(id):
    announcements = read_json(ANNOUNCEMENTS_FILE)
    filtered = [a for a in announcements if a['id'] != id]
    write_json(ANNOUNCEMENTS_FILE, filtered)
    return jsonify({'success': True})

@app.route('/api/projects', methods=['GET'])
def get_projects():
    projects = read_json(PROJECTS_FILE)
    for project in projects:
        project_dir = os.path.join(UPLOADS_DIR, str(project['id']))
        if os.path.exists(project_dir):
            project['fileCount'] = len(os.listdir(project_dir))
        else:
            project['fileCount'] = 0
    return jsonify(projects)

@app.route('/api/projects', methods=['POST'])
def create_project():
    name = request.form.get('name', '')
    description = request.form.get('description', '')
    projects = read_json(PROJECTS_FILE)
    new_project = {
        'id': str(int(datetime.now().timestamp() * 1000)),
        'name': name,
        'description': description,
        'createdAt': datetime.now().isoformat()
    }
    
    # 处理图片上传
    if 'image' in request.files:
        image = request.files['image']
        if image and allowed_file(image.filename):
            project_dir = os.path.join(UPLOADS_DIR, new_project['id'])
            image_dir = os.path.join(project_dir, 'image')
            os.makedirs(image_dir, exist_ok=True)
            
            filename = secure_filename(image.filename)
            image_path = os.path.join(image_dir, filename)
            image.save(image_path)
            new_project['image'] = filename
    else:
        project_dir = os.path.join(UPLOADS_DIR, new_project['id'])
        os.makedirs(project_dir, exist_ok=True)
    
    projects.append(new_project)
    write_json(PROJECTS_FILE, projects)
    return jsonify(new_project)

@app.route('/api/projects/<project_id>', methods=['DELETE'])
def delete_project(project_id):
    projects = read_json(PROJECTS_FILE)
    filtered = [p for p in projects if p['id'] != project_id]
    write_json(PROJECTS_FILE, filtered)
    project_dir = os.path.join(UPLOADS_DIR, project_id)
    if os.path.exists(project_dir):
        import shutil
        shutil.rmtree(project_dir)
    return jsonify({'success': True})

@app.route('/api/projects/<project_id>/files', methods=['GET'])
def get_files(project_id):
    project_dir = os.path.join(UPLOADS_DIR, project_id)
    path = request.args.get('path', '')
    target_dir = os.path.join(project_dir, path)
    
    if not os.path.exists(target_dir):
        return jsonify([])
    files = []
    for filename in os.listdir(target_dir):
        filepath = os.path.join(target_dir, filename)
        stat = os.stat(filepath)
        files.append({
            'name': filename,
            'size': stat.st_size,
            'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
            'type': os.path.splitext(filename)[1].lower(),
            'isDirectory': os.path.isdir(filepath),
            'path': os.path.join(path, filename)
        })
    return jsonify(files)

@app.route('/api/projects/<project_id>/upload', methods=['POST'])
def upload_files(project_id):
    if 'files' not in request.files:
        return jsonify({'error': 'No files'}), 400
    
    project_dir = os.path.join(UPLOADS_DIR, project_id)
    path = request.form.get('path', '')
    target_dir = os.path.join(project_dir, path)
    os.makedirs(target_dir, exist_ok=True)
    
    files = request.files.getlist('files')
    passwords = request.form.getlist('passwords')
    uploaded = []
    
    # 读取密码存储
    passwords_data = read_json(PASSWORD_FILE)
    
    for i, file in enumerate(files):
        if file and allowed_file(file.filename):
            filename = file.filename
            filepath = os.path.join(target_dir, filename)
            file.save(filepath)
            uploaded.append(filename)
            
            # 处理密码
            if i < len(passwords) and passwords[i]:
                file_key = f"{project_id}/{os.path.join(path, filename)}"
                passwords_data[file_key] = hash_password(passwords[i])
    
    # 保存密码
    if passwords_data:
        write_json(PASSWORD_FILE, passwords_data)
    
    # 上传完成后更新知识库
    if uploaded:
        try:
            update_knowledge_base()
        except Exception as e:
            print(f"更新知识库失败: {e}")
    
    return jsonify({'success': True, 'files': uploaded})

@app.route('/api/projects/<project_id>/files/<filename>', methods=['DELETE'])
def delete_file(project_id, filename):
    path = request.args.get('path', '')
    filepath = os.path.join(UPLOADS_DIR, project_id, path, filename)
    if os.path.exists(filepath):
        if os.path.isdir(filepath):
            import shutil
            shutil.rmtree(filepath)
        else:
            os.remove(filepath)
            
            # 删除密码
            passwords_data = read_json(PASSWORD_FILE)
            file_key = f"{project_id}/{os.path.join(path, filename)}"
            if file_key in passwords_data:
                del passwords_data[file_key]
                write_json(PASSWORD_FILE, passwords_data)
        
        return jsonify({'success': True})
    return jsonify({'error': 'File not found'}), 404

@app.route('/api/projects/<project_id>/create-folder', methods=['POST'])
def create_folder(project_id):
    data = request.get_json()
    folder_name = data.get('folderName')
    parent_path = data.get('parentPath', '')
    
    if not folder_name:
        return jsonify({'error': 'Folder name is required'}), 400
    
    project_dir = os.path.join(UPLOADS_DIR, project_id)
    folder_path = os.path.join(project_dir, parent_path, folder_name)
    
    try:
        os.makedirs(folder_path, exist_ok=True)
        return jsonify({'success': True, 'path': os.path.join(parent_path, folder_name)})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/projects/<project_id>/download/<filename>')
def download_file(project_id, filename):
    path = request.args.get('path', '')
    filepath = os.path.join(UPLOADS_DIR, project_id, path, filename)
    if not os.path.exists(filepath):
        return jsonify({'error': 'File not found'}), 404
    
    # 检查密码
    passwords_data = read_json(PASSWORD_FILE)
    file_key = f"{project_id}/{os.path.join(path, filename)}"
    
    if file_key in passwords_data:
        password = request.args.get('password')
        if not password or not verify_password(passwords_data[file_key], password):
            return jsonify({'error': 'Password required'}), 401
    
    return send_file(filepath, as_attachment=True, download_name=filename)

@app.route('/api/projects/<project_id>/export')
def export_project(project_id):
    project_dir = os.path.join(UPLOADS_DIR, project_id)
    if not os.path.exists(project_dir):
        return jsonify({'error': 'Project not found'}), 404
    
    memory_file = io.BytesIO()
    with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
        for filename in os.listdir(project_dir):
            filepath = os.path.join(project_dir, filename)
            zf.write(filepath, filename)
    memory_file.seek(0)
    
    return send_file(
        memory_file,
        mimetype='application/zip',
        as_attachment=True,
        download_name=f'project_{project_id}.zip'
    )

@app.route('/api/search')
def search():
    query = request.args.get('q', '').lower()
    if not query:
        return jsonify([])
    
    results = []
    projects = read_json(PROJECTS_FILE)
    
    for project in projects:
        project_dir = os.path.join(UPLOADS_DIR, str(project['id']))
        if not os.path.exists(project_dir):
            continue
        
        for filename in os.listdir(project_dir):
            filepath = os.path.join(project_dir, filename)
            ext = os.path.splitext(filename)[1].lower()
            
            if query in filename.lower():
                results.append({
                    'projectId': project['id'],
                    'projectName': project['name'],
                    'filename': filename,
                    'matchType': 'filename'
                })
                continue
            
            if ext in ['.txt', '.pdf', '.docx']:
                text = extract_text_from_file(filepath)
                if query in text.lower():
                    results.append({
                        'projectId': project['id'],
                        'projectName': project['name'],
                        'filename': filename,
                        'matchType': 'content'
                    })
    
    return jsonify(results)

@app.route('/api/knowledge/search')
def knowledge_search():
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify([])
    
    # 搜索知识库
    results = search_knowledge_base(query)
    
    # 格式化结果
    formatted_results = []
    for result in results:
        formatted_results.append({
            'id': result['id'],
            'filename': result['filename'],
            'projectId': result['project_id'],
            'score': result['score'],
            'content': result['content'],
            'matchType': 'knowledge'
        })
    
    return jsonify(formatted_results)

@app.route('/api/knowledge/update')
def knowledge_update():
    try:
        update_knowledge_base()
        return jsonify({'success': True, 'message': '知识库更新成功'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/uploads/<project_id>/<filename>')
def serve_upload(project_id, filename):
    filepath = os.path.join(UPLOADS_DIR, project_id, filename)
    if not os.path.exists(filepath):
        return jsonify({'error': 'File not found'}), 404
    
    # 检查密码
    passwords_data = read_json(PASSWORD_FILE)
    file_key = f"{project_id}/{filename}"
    
    if file_key in passwords_data:
        password = request.args.get('password')
        if not password or not verify_password(passwords_data[file_key], password):
            return jsonify({'error': 'Password required'}), 401
    
    return send_from_directory(os.path.join(UPLOADS_DIR, project_id), filename)

@app.route('/uploads/<project_id>/image/<filename>')
def serve_project_image(project_id, filename):
    return send_from_directory(os.path.join(UPLOADS_DIR, project_id, 'image'), filename)

if __name__ == '__main__':
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    print("=" * 50)
    print("Server started!")
    print("=" * 50)
    print("Local: http://localhost:5000")
    print("Network: http://<your-ip>:5000")
    print("Press Ctrl+C to stop")
    print("=" * 50)
    app.run(host='0.0.0.0', port=5000, debug=True)
