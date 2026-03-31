import os
import json
import re
from datetime import datetime
from docx import Document
import PyPDF2

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOADS_DIR = os.path.join(BASE_DIR, 'uploads')
KNOWLEDGE_BASE_DIR = os.path.join(BASE_DIR, 'knowledge_base')
KNOWLEDGE_INDEX_FILE = os.path.join(KNOWLEDGE_BASE_DIR, 'index.json')

os.makedirs(KNOWLEDGE_BASE_DIR, exist_ok=True)

def extract_text_from_file(filepath):
    ext = os.path.splitext(filepath)[1].lower()
    try:
        if ext == '.txt':
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
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
        print(f"Error extracting text from {filepath}: {e}")
    return ''

def create_knowledge_base():
    knowledge_items = []
    
    for project_id in os.listdir(UPLOADS_DIR):
        project_dir = os.path.join(UPLOADS_DIR, project_id)
        if not os.path.isdir(project_dir):
            continue
        
        for filename in os.listdir(project_dir):
            filepath = os.path.join(project_dir, filename)
            if os.path.isfile(filepath):
                # 跳过 image 目录
                if filename == 'image':
                    continue
                
                # 提取文件内容
                content = extract_text_from_file(filepath)
                
                # 生成知识条目
                knowledge_item = {
                    'id': f"{project_id}_{os.path.basename(filename)}",
                    'filename': filename,
                    'project_id': project_id,
                    'content': content,
                    'file_path': filepath.replace(BASE_DIR, ''),
                    'created_at': datetime.now().isoformat(),
                    'updated_at': datetime.now().isoformat()
                }
                knowledge_items.append(knowledge_item)
    
    # 保存知识库索引
    knowledge_base = {
        'created_at': datetime.now().isoformat(),
        'total_items': len(knowledge_items),
        'items': knowledge_items
    }
    
    with open(KNOWLEDGE_INDEX_FILE, 'w', encoding='utf-8') as f:
        json.dump(knowledge_base, f, ensure_ascii=False, indent=2)
    
    print(f"知识库创建完成，共 {len(knowledge_items)} 个文件")
    return knowledge_base

def search_knowledge_base(query, top_k=5):
    if not os.path.exists(KNOWLEDGE_INDEX_FILE):
        create_knowledge_base()
    
    with open(KNOWLEDGE_INDEX_FILE, 'r', encoding='utf-8') as f:
        knowledge_base = json.load(f)
    
    results = []
    query_lower = query.lower()
    
    for item in knowledge_base['items']:
        # 简单的关键词匹配
        if query_lower in item['content'].lower() or query_lower in item['filename'].lower():
            # 计算匹配分数（简单实现）
            score = 0
            if query_lower in item['content'].lower():
                score += 1
            if query_lower in item['filename'].lower():
                score += 2
            
            results.append({
                'id': item['id'],
                'filename': item['filename'],
                'project_id': item['project_id'],
                'score': score,
                'content': item['content'][:500] + '...' if len(item['content']) > 500 else item['content']
            })
    
    # 按分数排序
    results.sort(key=lambda x: x['score'], reverse=True)
    return results[:top_k]

def update_knowledge_base():
    """更新知识库，添加新文件"""
    if not os.path.exists(KNOWLEDGE_INDEX_FILE):
        return create_knowledge_base()
    
    with open(KNOWLEDGE_INDEX_FILE, 'r', encoding='utf-8') as f:
        existing_base = json.load(f)
    
    existing_ids = {item['id'] for item in existing_base['items']}
    new_items = []
    
    for project_id in os.listdir(UPLOADS_DIR):
        project_dir = os.path.join(UPLOADS_DIR, project_id)
        if not os.path.isdir(project_dir):
            continue
        
        for filename in os.listdir(project_dir):
            filepath = os.path.join(project_dir, filename)
            if os.path.isfile(filepath):
                if filename == 'image':
                    continue
                
                item_id = f"{project_id}_{os.path.basename(filename)}"
                if item_id not in existing_ids:
                    content = extract_text_from_file(filepath)
                    new_item = {
                        'id': item_id,
                        'filename': filename,
                        'project_id': project_id,
                        'content': content,
                        'file_path': filepath.replace(BASE_DIR, ''),
                        'created_at': datetime.now().isoformat(),
                        'updated_at': datetime.now().isoformat()
                    }
                    new_items.append(new_item)
    
    if new_items:
        existing_base['items'].extend(new_items)
        existing_base['total_items'] = len(existing_base['items'])
        existing_base['updated_at'] = datetime.now().isoformat()
        
        with open(KNOWLEDGE_INDEX_FILE, 'w', encoding='utf-8') as f:
            json.dump(existing_base, f, ensure_ascii=False, indent=2)
        
        print(f"知识库更新完成，新增 {len(new_items)} 个文件")
    else:
        print("知识库已是最新，无新文件")
    
    return existing_base

if __name__ == '__main__':
    print("初始化知识库...")
    create_knowledge_base()
    print("知识库初始化完成！")
