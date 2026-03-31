let projects = [];
let announcements = [];

document.addEventListener('DOMContentLoaded', () => {
    loadAnnouncements();
    loadProjects();
    
    document.getElementById('searchInput').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            performSearch();
        }
    });
});

async function loadAnnouncements() {
    try {
        const response = await fetch('/api/announcements');
        announcements = await response.json();
        renderAnnouncements();
    } catch (error) {
        console.error('加载提醒失败:', error);
    }
}

function renderAnnouncements() {
    const container = document.getElementById('announcementsList');
    
    if (announcements.length === 0) {
        container.innerHTML = '<div class="no-results">暂无重要提醒</div>';
        return;
    }
    
    container.innerHTML = announcements.map(a => `
        <div class="announcement-item ${a.priority === 'high' ? 'high-priority' : ''}">
            <div class="announcement-content">
                <span class="announcement-icon">${a.priority === 'high' ? '🔴' : '📢'}</span>
                <div>
                    <div class="announcement-text">${escapeHtml(a.content)}</div>
                    <div class="announcement-date">${formatDate(a.date)}</div>
                </div>
            </div>
            <div class="announcement-actions">
                <button onclick="deleteAnnouncement(${a.id})" title="删除">×</button>
            </div>
        </div>
    `).join('');
}

async function loadProjects() {
    try {
        const response = await fetch('/api/projects');
        projects = await response.json();
        renderProjects();
    } catch (error) {
        console.error('加载项目失败:', error);
    }
}

function renderProjects() {
    const container = document.getElementById('projectsList');
    
    if (projects.length === 0) {
        container.innerHTML = '<div class="no-results">暂无项目，点击"新建项目"创建第一个项目文件夹</div>';
        return;
    }
    
    const localImages = {
        '北滘蚬华': '蚬华项目.jpg',
        '三水昊通': '三水项目.jpg',
        '鄱阳星引力': '鄱阳星引力项目.jpg',
        '湖南德科': '湖南德科项目.jpg'
    };
    
    container.innerHTML = projects.map(p => {
        const localImage = localImages[p.name];
        let bgStyle = '';
        
        if (localImage) {
            bgStyle = `style="background-image: url('${localImage}'); background-size: cover; background-position: center;"`;
        } else if (p.image) {
            bgStyle = `style="background-image: url('/uploads/${p.id}/image/${p.image}'); background-size: cover; background-position: center;"`;
        }
        
        return `
        <div class="project-card ${localImage || p.image ? 'has-bg-image' : ''}" onclick="openProject('${p.id}')" ${bgStyle}>
            <div class="project-icon"></div>
            <div class="project-name">${escapeHtml(p.name)}</div>
            <div class="project-description">${escapeHtml(p.description || '暂无描述')}</div>
            <div class="project-meta">
                <span class="file-count">
                    <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                        <polyline points="14 2 14 8 20 8"/>
                    </svg>
                    ${p.fileCount} 个文件
                </span>
                <div class="project-actions" onclick="event.stopPropagation()">
                    <button onclick="exportProject('${p.id}')" title="导出">导出</button>
                    <button class="delete" onclick="deleteProject('${p.id}')" title="删除">删除</button>
                </div>
            </div>
        </div>
    `}).join('');
}

function showAddProjectModal() {
    document.getElementById('addProjectModal').style.display = 'flex';
    document.getElementById('projectName').value = '';
    document.getElementById('projectDescription').value = '';
    document.getElementById('projectImage').value = '';
    
    // 添加上传区域的点击事件
    const uploadArea = document.querySelector('#addProjectModal .upload-area');
    const fileInput = document.getElementById('projectImage');
    
    uploadArea.addEventListener('click', () => fileInput.click());
    
    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.style.borderColor = '#3b82f6';
    });
    
    uploadArea.addEventListener('dragleave', () => {
        uploadArea.style.borderColor = '#cbd5e1';
    });
    
    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.style.borderColor = '#cbd5e1';
        if (e.dataTransfer.files.length > 0) {
            fileInput.files = e.dataTransfer.files;
        }
    });
}

function closeAddProjectModal() {
    document.getElementById('addProjectModal').style.display = 'none';
}

async function createProject() {
    const name = document.getElementById('projectName').value.trim();
    const description = document.getElementById('projectDescription').value.trim();
    const projectImage = document.getElementById('projectImage').files[0];
    
    if (!name) {
        alert('请输入项目名称');
        return;
    }
    
    try {
        const formData = new FormData();
        formData.append('name', name);
        formData.append('description', description);
        if (projectImage) {
            formData.append('image', projectImage);
        }
        
        const response = await fetch('/api/projects', {
            method: 'POST',
            body: formData
        });
        
        if (response.ok) {
            closeAddProjectModal();
            loadProjects();
        }
    } catch (error) {
        console.error('创建项目失败:', error);
    }
}

async function deleteProject(projectId) {
    if (!confirm('确定要删除此项目及其所有文件吗？')) return;
    
    try {
        await fetch(`/api/projects/${projectId}`, { method: 'DELETE' });
        loadProjects();
    } catch (error) {
        console.error('删除项目失败:', error);
    }
}

function exportProject(projectId) {
    window.location.href = `/api/projects/${projectId}/export`;
}

function openProject(projectId) {
    window.location.href = `project.html?id=${projectId}`;
}

function showAddAnnouncementModal() {
    document.getElementById('addAnnouncementModal').style.display = 'flex';
    document.getElementById('announcementContent').value = '';
    document.getElementById('announcementPriority').value = 'normal';
}

function closeAddAnnouncementModal() {
    document.getElementById('addAnnouncementModal').style.display = 'none';
}

async function createAnnouncement() {
    const content = document.getElementById('announcementContent').value.trim();
    const priority = document.getElementById('announcementPriority').value;
    
    if (!content) {
        alert('请输入提醒内容');
        return;
    }
    
    try {
        const response = await fetch('/api/announcements', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ content, priority })
        });
        
        if (response.ok) {
            closeAddAnnouncementModal();
            loadAnnouncements();
        }
    } catch (error) {
        console.error('添加提醒失败:', error);
    }
}

async function deleteAnnouncement(id) {
    if (!confirm('确定要删除此提醒吗？')) return;
    
    try {
        await fetch(`/api/announcements/${id}`, { method: 'DELETE' });
        loadAnnouncements();
    } catch (error) {
        console.error('删除提醒失败:', error);
    }
}

async function performSearch() {
    const query = document.getElementById('searchInput').value.trim();
    if (!query) {
        alert('请输入搜索内容');
        return;
    }
    
    try {
        // 并行搜索文件和知识库
        const [fileResults, knowledgeResults] = await Promise.all([
            fetch(`/api/search?q=${encodeURIComponent(query)}`).then(r => r.json()),
            fetch(`/api/knowledge/search?q=${encodeURIComponent(query)}`).then(r => r.json())
        ]);
        
        // 合并结果
        const allResults = [...fileResults, ...knowledgeResults];
        showSearchResults(allResults);
    } catch (error) {
        console.error('搜索失败:', error);
    }
}

function showSearchResults(results) {
    const modal = document.getElementById('searchResults');
    const list = document.getElementById('searchResultsList');
    
    if (results.length === 0) {
        list.innerHTML = '<div class="no-results">未找到匹配的文件</div>';
    } else {
        list.innerHTML = results.map(r => {
            if (r.matchType === 'knowledge') {
                return `
                    <div class="search-result-item" onclick="openFileInNewWindow('${r.projectId}', '${escapeHtml(r.filename)}')" style="cursor: pointer;">
                        <div class="result-info">
                            <div class="result-icon">
                                <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="#10b981" stroke-width="2">
                                    <circle cx="12" cy="12" r="10"/>
                                    <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/>
                                    <path d="M12 17h.01"/>
                                </svg>
                            </div>
                            <div class="result-details">
                                <h4>${escapeHtml(r.filename)}</h4>
                                <p>知识库匹配</p>
                                <p style="font-size: 0.8rem; color: #666; margin-top: 8px; line-height: 1.4;">${escapeHtml(r.content)}</p>
                            </div>
                            <span class="match-badge" style="background: #d1fae5; color: #059669;">知识库</span>
                        </div>
                        <div class="result-actions">
                            <button onclick="event.stopPropagation(); openFileInNewWindow('${r.projectId}', '${escapeHtml(r.filename)}')">打开文件</button>
                        </div>
                    </div>
                `;
            } else {
                return `
                    <div class="search-result-item" onclick="openFileInNewWindow('${r.projectId}', '${escapeHtml(r.filename)}')" style="cursor: pointer;">
                        <div class="result-info">
                            <div class="result-icon">
                                <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="#3b82f6" stroke-width="2">
                                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                                    <polyline points="14 2 14 8 20 8"/>
                                </svg>
                            </div>
                            <div class="result-details">
                                <h4>${escapeHtml(r.filename)}</h4>
                                <p>项目: ${escapeHtml(r.projectName)}</p>
                            </div>
                            <span class="match-badge">${r.matchType === 'filename' ? '文件名匹配' : '内容匹配'}</span>
                        </div>
                        <div class="result-actions">
                            <button onclick="event.stopPropagation(); openFileInNewWindow('${r.projectId}', '${escapeHtml(r.filename)}')">打开文件</button>
                        </div>
                    </div>
                `;
            }
        }).join('');
    }
    
    modal.style.display = 'flex';
}

function openFileInNewWindow(projectId, filename) {
    const fileUrl = `/uploads/${projectId}/${encodeURIComponent(filename)}`;
    window.open(fileUrl, '_blank');
}

function closeSearchResults() {
    document.getElementById('searchResults').style.display = 'none';
}

function goToProject(projectId) {
    window.location.href = `project.html?id=${projectId}`;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
    });
}
