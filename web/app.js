document.addEventListener('DOMContentLoaded', () => {
    // API Configurations
    const API_BASE_URL = 'http://localhost:8000';
    let isServerOnline = false;
    
    // DOM Selectors
    const chatInput = document.getElementById('chatInput');
    const sendBtn = document.getElementById('sendBtn');
    const messagesContainer = document.getElementById('messagesContainer');
    const statusDot = document.getElementById('statusDot');
    const statusText = document.getElementById('statusText');
    
    // Sidebar DOM Selectors
    const toggleSidebarBtn = document.getElementById('toggleSidebarBtn');
    const sidebar = document.getElementById('sidebar');
    const uploadZone = document.getElementById('uploadZone');
    const fileInput = document.getElementById('fileInput');
    const uploadProgressContainer = document.getElementById('uploadProgressContainer');
    const uploadFilename = document.getElementById('uploadFilename');
    const progressBar = document.getElementById('progressBar');
    const uploadStatusText = document.getElementById('uploadStatusText');
    const documentList = document.getElementById('documentList');
    const docCount = document.getElementById('docCount');

    // Initialize Lucide Icons
    lucide.createIcons();

    // Auto-resize textarea as user types
    chatInput.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = (this.scrollHeight - 4) + 'px';
    });

    // Toggle Sidebar
    toggleSidebarBtn.addEventListener('click', () => {
        sidebar.classList.toggle('collapsed');
    });

    // Check Backend Server Status
    async function checkServerStatus() {
        const wasOffline = !isServerOnline;
        try {
            const response = await fetch(`${API_BASE_URL}/`, {
                method: 'GET',
                signal: AbortSignal.timeout(3000) // 3s timeout
            });
            
            if (response.ok) {
                const data = await response.json();
                if (data.status === 'healthy') {
                    statusDot.className = 'status-dot connected';
                    statusText.textContent = 'Đang trực tuyến';
                    isServerOnline = true;
                    
                    // Fetch documents if server just came online
                    if (wasOffline) {
                        fetchDocuments();
                    }
                    return true;
                }
            }
            throw new Error('Server unhealthy');
        } catch (error) {
            statusDot.className = 'status-dot disconnected';
            statusText.textContent = 'Mất kết nối API';
            isServerOnline = false;
            return false;
        }
    }

    // Run health check initially and then every 10 seconds
    checkServerStatus();
    setInterval(checkServerStatus, 10000);

    // Fetch and display uploaded documents
    async function fetchDocuments() {
        if (!isServerOnline) return;
        
        try {
            const response = await fetch(`${API_BASE_URL}/document/get-list-document`);
            if (!response.ok) throw new Error('Failed to load documents');
            
            const data = await response.json();
            const docs = data.list_document || [];
            
            // Update document counter badge
            docCount.textContent = docs.length;
            
            if (docs.length === 0) {
                documentList.innerHTML = `
                    <div class="empty-docs">
                        <i data-lucide="inbox"></i>
                        <p>Chưa có tài liệu nào.<br>Hãy tải lên tài liệu để huấn luyện bot!</p>
                    </div>
                `;
                lucide.createIcons();
                return;
            }
            
            // Render Document items
            documentList.innerHTML = docs.map(doc => {
                const docId = doc._id;
                const filename = doc.filename;
                const size = formatBytes(doc.file_size_byte);
                const fileType = doc.file_type || filename.split('.').pop().toLowerCase();
                
                // Select file icon based on extension
                let iconName = 'file-text';
                if (fileType === 'pdf') iconName = 'file-text';
                else if (fileType === 'docx') iconName = 'file-type-2';
                else if (fileType === 'txt') iconName = 'file-code';
                else if (fileType === 'md') iconName = 'file-edit';
                
                return `
                    <div class="document-item" id="doc-item-${docId}">
                        <div class="doc-info">
                            <i data-lucide="${iconName}" class="doc-type-icon"></i>
                            <div class="doc-details">
                                <span class="doc-name" title="${escapeHtml(filename)}">${escapeHtml(filename)}</span>
                                <span class="doc-meta">v${doc.version || 1} • ${size}</span>
                            </div>
                        </div>
                        <button class="doc-action-btn delete-doc-btn" data-id="${docId}" data-name="${escapeHtml(filename)}" title="Xóa tài liệu">
                            <i data-lucide="trash-2"></i>
                        </button>
                    </div>
                `;
            }).join('');
            
            // Add Delete Event Listeners
            document.querySelectorAll('.delete-doc-btn').forEach(btn => {
                btn.addEventListener('click', (e) => {
                    const id = btn.getAttribute('data-id');
                    const name = btn.getAttribute('data-name');
                    handleDeleteDocument(id, name);
                });
            });
            
            lucide.createIcons();
        } catch (error) {
            console.error('Error fetching documents:', error);
            documentList.innerHTML = `
                <div class="empty-docs" style="color: #ef4444;">
                    <i data-lucide="alert-triangle"></i>
                    <p>Lỗi tải danh sách tài liệu</p>
                </div>
            `;
            lucide.createIcons();
        }
    }

    // Delete Document Action
    async function handleDeleteDocument(documentId, filename) {
        if (!confirm(`Bạn có chắc chắn muốn xóa tài liệu "${filename}" khỏi cơ sở tri thức? Hành động này sẽ xóa toàn bộ vector lưu trữ.`)) {
            return;
        }

        const docItem = document.getElementById(`doc-item-${documentId}`);
        if (docItem) {
            docItem.style.opacity = '0.5';
            docItem.style.pointerEvents = 'none';
        }

        try {
            const response = await fetch(`${API_BASE_URL}/document/delete-document/${documentId}`, {
                method: 'DELETE'
            });

            if (!response.ok) throw new Error('Không thể xóa tài liệu');
            
            // Refresh list
            fetchDocuments();
        } catch (error) {
            alert(`Lỗi: ${error.message}`);
            if (docItem) {
                docItem.style.opacity = '1';
                docItem.style.pointerEvents = 'auto';
            }
        }
    }

    // Drag and Drop Logic
    uploadZone.addEventListener('click', () => fileInput.click());
    
    uploadZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadZone.classList.add('dragover');
    });
    
    ['dragleave', 'dragend', 'drop'].forEach(eventName => {
        uploadZone.addEventListener(eventName, () => {
            uploadZone.classList.remove('dragover');
        });
    });
    
    uploadZone.addEventListener('drop', (e) => {
        e.preventDefault();
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            handleUploadFile(files[0]);
        }
    });

    fileInput.addEventListener('change', (e) => {
        const files = e.target.files;
        if (files.length > 0) {
            handleUploadFile(files[0]);
            fileInput.value = ''; // Reset
        }
    });

    // Upload File Action
    function handleUploadFile(file) {
        if (!isServerOnline) {
            alert('Vui lòng kiểm tra lại kết nối. Máy chủ API đang ngoại tuyến!');
            return;
        }

        const allowedExtensions = ['pdf', 'docx', 'txt', 'md'];
        const extension = file.name.split('.').pop().toLowerCase();
        
        if (!allowedExtensions.includes(extension)) {
            alert(`Định dạng tệp không hỗ trợ! Chỉ cho phép: ${allowedExtensions.join(', ').toUpperCase()}`);
            return;
        }

        const maxSize = 50 * 1024 * 1024; // 50MB
        if (file.size > maxSize) {
            alert('Dung lượng tệp vượt quá giới hạn cho phép (Tối đa 50MB)!');
            return;
        }

        // Show progress UI
        uploadProgressContainer.style.display = 'flex';
        uploadFilename.textContent = file.name;
        progressBar.style.width = '0%';
        uploadStatusText.textContent = 'Đang chuẩn bị tải lên...';
        uploadStatusText.style.color = 'var(--accent-secondary)';

        // Prepare Form Data
        const formData = new FormData();
        formData.append('file', file);

        // Upload using XMLHttpRequest to monitor progress
        const xhr = new XMLHttpRequest();
        xhr.open('POST', `${API_BASE_URL}/document/upload-document`, true);

        // Track upload progress
        xhr.upload.addEventListener('progress', (e) => {
            if (e.lengthComputable) {
                const percentComplete = Math.round((e.loaded / e.total) * 100);
                progressBar.style.width = percentComplete + '%';
                if (percentComplete < 100) {
                    uploadStatusText.textContent = `Đang tải lên: ${percentComplete}%`;
                } else {
                    uploadStatusText.textContent = 'Đang phân tích & trích xuất văn bản...';
                }
            }
        });

        // Response handler
        xhr.onload = function() {
            if (xhr.status === 200) {
                try {
                    const result = JSON.parse(xhr.responseText);
                    progressBar.style.width = '100%';
                    uploadStatusText.textContent = 'Tải lên thành công!';
                    uploadStatusText.style.color = '#10b981'; // Green success color
                    
                    // Refresh document list
                    fetchDocuments();

                    // Hide progress after 2.5s
                    setTimeout(() => {
                        uploadProgressContainer.style.animation = 'slideDown 0.3s ease reverse forwards';
                        setTimeout(() => {
                            uploadProgressContainer.style.display = 'none';
                            uploadProgressContainer.style.animation = '';
                        }, 300);
                    }, 2500);
                } catch (e) {
                    showUploadError('Phản hồi từ máy chủ không hợp lệ.');
                }
            } else {
                let errorMsg = 'Tải lên thất bại.';
                try {
                    const errorObj = JSON.parse(xhr.responseText);
                    errorMsg = errorObj.detail || errorMsg;
                } catch (e) {}
                showUploadError(errorMsg);
            }
        };

        xhr.onerror = function() {
            showUploadError('Kết nối tới máy chủ bị gián đoạn.');
        };

        xhr.send(formData);
    }

    function showUploadError(message) {
        progressBar.style.width = '100%';
        progressBar.style.background = '#ef4444'; // Red error color
        uploadStatusText.textContent = `Lỗi: ${message}`;
        uploadStatusText.style.color = '#f87171';
    }

    // Send Message Action
    async function handleSendMessage() {
        const query = chatInput.value.trim();
        if (!query) return;

        // Reset input height & value
        chatInput.value = '';
        chatInput.style.height = 'auto';
        chatInput.focus();

        // 1. Add User Message to Chat Window
        appendUserMessage(query);
        
        // Scroll to bottom
        scrollToBottom();

        // 2. Add Bot Message with typing indicator
        const botMessageId = 'bot-response-' + Date.now();
        appendBotLoadingMessage(botMessageId);
        scrollToBottom();

        try {
            // 3. Make POST request to Chat API
            const chatUrl = new URL(`${API_BASE_URL}/chat/chat`);
            chatUrl.searchParams.append('question', query);

            const response = await fetch(chatUrl, {
                method: 'POST',
                headers: {
                    'Accept': 'application/json'
                }
            });

            if (!response.ok) {
                const errDetail = await response.text();
                throw new Error(`Server error (${response.status}): ${errDetail || response.statusText}`);
            }

            const data = await response.json();
            
            // 4. Update loading bubble with real response
            renderBotResponse(botMessageId, data.answer, data.sources);
        } catch (error) {
            console.error('Chat Error:', error);
            renderBotError(botMessageId, error.message);
        } finally {
            scrollToBottom();
        }
    }

    // Event Listeners for sending message
    sendBtn.addEventListener('click', handleSendMessage);
    
    chatInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSendMessage();
        }
    });

    // Helper: Scroll to bottom of message container
    function scrollToBottom() {
        messagesContainer.scrollTo({
            top: messagesContainer.scrollHeight,
            behavior: 'smooth'
        });
    }

    // Helper: Get clean file name from path
    function getFileName(filePath) {
        if (!filePath) return 'Tài liệu';
        return filePath.split(/[/\\]/).pop();
    }

    // Helper: Format Bytes to human readable
    function formatBytes(bytes, decimals = 1) {
        if (bytes === 0) return '0 B';
        const k = 1024;
        const dm = decimals < 0 ? 0 : decimals;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
    }

    // Helper: Append User Message
    function appendUserMessage(text) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message user-msg';
        
        messageDiv.innerHTML = `
            <div class="message-avatar">
                <i data-lucide="user"></i>
            </div>
            <div class="message-content-wrapper">
                <div class="message-sender">Bạn</div>
                <div class="message-content">
                    <p>${escapeHtml(text).replace(/\n/g, '<br>')}</p>
                </div>
            </div>
        `;
        
        messagesContainer.appendChild(messageDiv);
        lucide.createIcons();
    }

    // Helper: Append Bot Loading Bubble
    function appendBotLoadingMessage(id) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message system-msg';
        messageDiv.id = id;
        
        messageDiv.innerHTML = `
            <div class="message-avatar">
                <i data-lucide="bot"></i>
            </div>
            <div class="message-content-wrapper">
                <div class="message-sender">ChatML Bot</div>
                <div class="message-content">
                    <div class="typing-indicator">
                        <span class="typing-dot"></span>
                        <span class="typing-dot"></span>
                        <span class="typing-dot"></span>
                    </div>
                </div>
            </div>
        `;
        
        messagesContainer.appendChild(messageDiv);
        lucide.createIcons();
    }

    // Helper: Render Response in Bot Bubble
    function renderBotResponse(id, markdownText, sources) {
        const botBubble = document.getElementById(id);
        if (!botBubble) return;

        const contentDiv = botBubble.querySelector('.message-content');
        
        // Parse markdown to HTML
        let parsedHtml = marked.parse(markdownText);
        contentDiv.innerHTML = parsedHtml;

        // Render sources/citations if present
        if (sources && sources.length > 0) {
            const sourcesPanel = document.createElement('div');
            sourcesPanel.className = 'sources-panel';
            
            // Deduplicate sources to show unique document files
            const uniqueSources = [];
            const seenDocs = new Set();
            
            sources.forEach(src => {
                const docName = getFileName(src.document_id);
                const key = `${docName}-${src.chunk_id}`;
                if (!seenDocs.has(key)) {
                    seenDocs.add(key);
                    uniqueSources.push({
                        name: docName,
                        chunk: src.chunk_id
                    });
                }
            });

            if (uniqueSources.length > 0) {
                sourcesPanel.innerHTML = `
                    <div class="sources-title">
                        <i data-lucide="book-open" style="width: 12px; height: 12px;"></i>
                        Tài liệu tham khảo:
                    </div>
                    <div class="sources-list">
                        ${uniqueSources.map(src => `
                            <span class="source-badge" title="Mã đoạn: ${src.chunk}">
                                <i data-lucide="file-text"></i>
                                ${src.name}
                            </span>
                        `).join('')}
                    </div>
                `;
                contentDiv.appendChild(sourcesPanel);
            }
        }

        // Apply syntax highlighting
        Prism.highlightAllUnder(contentDiv);
        
        // Re-run Lucide icons for new badges/icons
        lucide.createIcons();
    }

    // Helper: Render Error in Bot Bubble
    function renderBotError(id, errorMessage) {
        const botBubble = document.getElementById(id);
        if (!botBubble) return;

        const contentDiv = botBubble.querySelector('.message-content');
        contentDiv.innerHTML = `
            <div style="color: #f87171; display: flex; align-items: flex-start; gap: 10px;">
                <i data-lucide="alert-circle" style="flex-shrink: 0; margin-top: 2px;"></i>
                <div>
                    <strong>Lỗi kết nối hoặc xử lý từ API!</strong><br>
                    <span style="font-size: 0.85rem; opacity: 0.9;">${escapeHtml(errorMessage)}</span>
                    <p style="margin-top: 8px; font-size: 0.8rem; opacity: 0.7;">
                        Hãy kiểm tra xem ứng dụng FastAPI đã được khởi động chưa (<code>uvicorn app.main:app --reload</code>) và các dịch vụ Docker (MongoDB, Qdrant) đã chạy.
                    </p>
                </div>
            </div>
        `;
        
        lucide.createIcons();
    }

    // Helper: Escape HTML to prevent XSS
    function escapeHtml(text) {
        const map = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;'
        };
        return text.replace(/[&<>"']/g, function(m) { return map[m]; });
    }
});
