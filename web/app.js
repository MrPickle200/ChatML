document.addEventListener('DOMContentLoaded', () => {
    // Configure Marked with KaTeX extension
    if (typeof markedKatex !== 'undefined') {
        marked.use(markedKatex({
            throwOnError: false,
            nonStandard: true
        }));
    } else if (window.markedKatex) {
        marked.use(window.markedKatex({
            throwOnError: false,
            nonStandard: true
        }));
    }

    // API Configurations
    const API_BASE_URL = 'http://localhost:8000';
    let isServerOnline = false;
    const documentNameCache = {};
    
    // DOM Selectors
    const chatInput = document.getElementById('chatInput');
    const sendBtn = document.getElementById('sendBtn');
    const messagesContainer = document.getElementById('messagesContainer');
    const statusDot = document.getElementById('statusDot');
    const statusText = document.getElementById('statusText');
    const chatDatasetSelect = document.getElementById('chatDatasetSelect');
    
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
    const uploadDatasetSelect = document.getElementById('uploadDatasetSelect');
    const createDatasetBtn = document.getElementById('createDatasetBtn');

    // Tabs & Conversations DOM Selectors
    const conversationsTabBtn = document.getElementById('conversationsTabBtn');
    const documentsTabBtn = document.getElementById('documentsTabBtn');
    const conversationsTabContent = document.getElementById('conversationsTabContent');
    const documentsTabContent = document.getElementById('documentsTabContent');
    const newChatBtn = document.getElementById('newChatBtn');
    const conversationList = document.getElementById('conversationList');
    const inputPanel = document.querySelector('.input-panel');

    let currentConversationId = null;

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

    // Tab switching logic
    conversationsTabBtn.addEventListener('click', () => {
        conversationsTabBtn.classList.add('active');
        documentsTabBtn.classList.remove('active');
        conversationsTabContent.classList.remove('hidden');
        documentsTabContent.classList.add('hidden');
    });

    documentsTabBtn.addEventListener('click', () => {
        documentsTabBtn.classList.add('active');
        conversationsTabBtn.classList.remove('active');
        documentsTabContent.classList.remove('hidden');
        conversationsTabContent.classList.add('hidden');
    });

    // New Chat logic
    newChatBtn.addEventListener('click', () => {
        currentConversationId = null;
        
        // Remove active class from all conversation items
        document.querySelectorAll('.conversation-item').forEach(item => {
            item.classList.remove('active');
        });

        // Reset chat window to welcome message
        resetChatWindow();
    });

    function resetChatWindow() {
        messagesContainer.innerHTML = `
            <div class="message system-msg">
                <div class="message-avatar">
                    <i data-lucide="bot"></i>
                </div>
                <div class="message-content-wrapper">
                    <div class="message-sender">ChatML Bot</div>
                    <div class="message-content">
                        <p>Xin chào! Tôi là <strong>ChatML</strong>, trợ lý học tập Machine Learning của bạn. Hãy tải tài liệu của bạn lên ở thanh bên trái để tôi phân tích, sau đó đặt câu hỏi cho tôi về bất kỳ tài liệu nào nhé!</p>
                    </div>
                </div>
            </div>
        `;
        lucide.createIcons();
    }

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
                    
                    // Fetch documents and conversations if server just came online
                    if (wasOffline) {
                        fetchDocuments();
                        fetchConversations();
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

    // Fetch and display uploaded documents grouped by dataset
    async function fetchDocuments() {
        if (!isServerOnline) return;
        
        try {
            // 1. Fetch datasets
            const datasetResponse = await fetch(`${API_BASE_URL}/document/list-dataset`);
            if (!datasetResponse.ok) throw new Error('Không thể tải danh sách bộ dữ liệu');
            const datasetData = await datasetResponse.json();
            const datasets = datasetData.list_dataset || [];

            // Update Dataset counts
            docCount.textContent = datasets.length;

            // Save selected values from dropdowns before rebuilding options
            const prevUploadSelect = uploadDatasetSelect ? uploadDatasetSelect.value : 'null';
            const prevChatSelect = chatDatasetSelect ? chatDatasetSelect.value : 'null';

            // Rebuild uploadDatasetSelect options
            if (uploadDatasetSelect) {
                uploadDatasetSelect.innerHTML = '<option value="null">-- Tạo tự động --</option>';
                datasets.forEach(ds => {
                    const name = (ds.name === 'blank' || !ds.name) ? `Bộ dữ liệu #${ds._id.substring(0, 6)}` : ds.name;
                    uploadDatasetSelect.innerHTML += `<option value="${ds._id}">${escapeHtml(name)}</option>`;
                });
                // Restore previous value if exists
                if (Array.from(uploadDatasetSelect.options).some(opt => opt.value === prevUploadSelect)) {
                    uploadDatasetSelect.value = prevUploadSelect;
                }
            }

            // Rebuild chatDatasetSelect options
            if (chatDatasetSelect) {
                chatDatasetSelect.innerHTML = '<option value="null">Tất cả tài liệu (Default)</option>';
                datasets.forEach(ds => {
                    const name = (ds.name === 'blank' || !ds.name) ? `Bộ dữ liệu #${ds._id.substring(0, 6)}` : ds.name;
                    chatDatasetSelect.innerHTML += `<option value="${ds._id}">${escapeHtml(name)}</option>`;
                });
                // Restore previous value if exists
                if (Array.from(chatDatasetSelect.options).some(opt => opt.value === prevChatSelect)) {
                    chatDatasetSelect.value = prevChatSelect;
                }
            }

            if (datasets.length === 0) {
                documentList.innerHTML = `
                    <div class="empty-docs">
                        <i data-lucide="inbox"></i>
                        <p>Chưa có bộ dữ liệu nào.<br>Bấm nút (+) ở trên để tạo mới!</p>
                    </div>
                `;
                lucide.createIcons();
                return;
            }

            // Render Dataset list (documents nested inside will load on demand)
            documentList.innerHTML = datasets.map(ds => {
                const dsId = ds._id;
                const dsName = (ds.name === 'blank' || !ds.name) ? `Bộ dữ liệu #${dsId.substring(0, 6)}` : ds.name;

                return `
                    <div class="dataset-item" id="dataset-item-${dsId}">
                        <div class="dataset-header" onclick="toggleDataset('${dsId}')">
                            <div class="dataset-title-group">
                                <i data-lucide="chevron-right" class="dataset-toggle-icon"></i>
                                <span class="dataset-name" title="${escapeHtml(dsName)}">${escapeHtml(dsName)}</span>
                            </div>
                            <div class="dataset-actions" onclick="event.stopPropagation();">
                                <button class="dataset-action-btn rename-dataset-btn" data-id="${dsId}" data-name="${escapeHtml(dsName)}" title="Đổi tên bộ dữ liệu">
                                    <i data-lucide="edit-3" style="width: 12px; height: 12px;"></i>
                                </button>
                                <button class="dataset-action-btn delete-dataset-btn" data-id="${dsId}" data-name="${escapeHtml(dsName)}" title="Xóa bộ dữ liệu">
                                    <i data-lucide="trash-2" style="width: 12px; height: 12px;"></i>
                                </button>
                            </div>
                        </div>
                        <div class="dataset-docs collapsed" id="dataset-docs-${dsId}" data-loaded="false">
                            <div class="empty-docs" style="padding: 10px 0; opacity: 0.6; font-size: 0.7rem;">
                                <p>Nhấp để tải danh sách tài liệu...</p>
                            </div>
                        </div>
                    </div>
                `;
            }).join('');

            // Add Delete Dataset Listeners
            document.querySelectorAll('.delete-dataset-btn').forEach(btn => {
                btn.addEventListener('click', (e) => {
                    const id = btn.getAttribute('data-id');
                    const name = btn.getAttribute('data-name');
                    handleDeleteDataset(id, name);
                });
            });

            // Add Rename Dataset Listeners
            document.querySelectorAll('.rename-dataset-btn').forEach(btn => {
                btn.addEventListener('click', (e) => {
                    const id = btn.getAttribute('data-id');
                    const name = btn.getAttribute('data-name');
                    handleRenameDataset(id, name);
                });
            });

            lucide.createIcons();
        } catch (error) {
            console.error('Error fetching datasets:', error);
            documentList.innerHTML = `
                <div class="empty-docs" style="color: #ef4444;">
                    <i data-lucide="alert-triangle"></i>
                    <p>Lỗi tải danh sách bộ dữ liệu</p>
                </div>
            `;
            lucide.createIcons();
        }
    }

    // Fetch and display conversations
    async function fetchConversations() {
        if (!isServerOnline) return;

        try {
            const response = await fetch(`${API_BASE_URL}/chat/list-conversation`);
            if (!response.ok) throw new Error('Failed to load conversations');

            const conversations = await response.json();
            
            if (conversations.length === 0) {
                conversationList.innerHTML = `
                    <div class="empty-conversations">
                        <i data-lucide="message-square-dashed"></i>
                        <p>Chưa có cuộc trò chuyện nào.<br>Bấm nút trên để tạo mới!</p>
                    </div>
                `;
                lucide.createIcons();
                return;
            }

            // Sắp xếp conversations theo thời gian updated_at (hoặc created_at) mới nhất lên đầu
            conversations.sort((a, b) => new Date(b.updated_at || b.created_at) - new Date(a.updated_at || a.created_at));

            // Render Conversation items
            conversationList.innerHTML = conversations.map(conv => {
                const convId = conv._id;
                const isActive = convId === currentConversationId ? 'active' : '';
                
                // Định dạng thời gian
                const dateObj = new Date(conv.updated_at || conv.created_at);
                const timeStr = dateObj.toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' });
                const dateStr = dateObj.toLocaleDateString('vi-VN', { day: '2-digit', month: '2-digit' });
                const displayTime = `${timeStr} ${dateStr}`;

                // Rút ngắn tên cuộc trò chuyện
                let title = conv.title || 'Cuộc trò chuyện mới';
                if (title === 'new conversation') {
                    title = `Cuộc trò chuyện #${convId.substring(0, 6)}`;
                }

                return `
                    <div class="conversation-item ${isActive}" id="conv-item-${convId}" data-id="${convId}">
                        <div class="conv-info">
                            <i data-lucide="message-square" class="conv-icon"></i>
                            <div class="conv-details">
                                <span class="conv-title" title="${escapeHtml(title)}">${escapeHtml(title)}</span>
                                <span class="conv-meta">${displayTime}</span>
                            </div>
                        </div>
                        <button class="conv-action-btn delete-conv-btn" data-id="${convId}" title="Xóa hội thoại" onclick="event.stopPropagation();">
                            <i data-lucide="trash-2"></i>
                        </button>
                    </div>
                `;
            }).join('');

            // Thêm sự kiện click cho từng conversation item
            document.querySelectorAll('.conversation-item').forEach(item => {
                item.addEventListener('click', () => {
                    const id = item.getAttribute('data-id');
                    handleSelectConversation(id);
                });
            });

            // Thêm sự kiện click cho nút xóa conversation
            document.querySelectorAll('.delete-conv-btn').forEach(btn => {
                btn.addEventListener('click', (e) => {
                    e.stopPropagation(); // Ngăn sự kiện click lan truyền lên parent item
                    const id = btn.getAttribute('data-id');
                    handleDeleteConversation(id);
                });
            });

            lucide.createIcons();
        } catch (error) {
            console.error('Error fetching conversations:', error);
            conversationList.innerHTML = `
                <div class="empty-conversations" style="color: #ef4444;">
                    <i data-lucide="alert-triangle"></i>
                    <p>Lỗi tải danh sách hội thoại</p>
                </div>
            `;
            lucide.createIcons();
        }
    }

    // Select Conversation Action
    async function handleSelectConversation(conversationId) {
        if (conversationId === currentConversationId) return;

        // Set active class
        document.querySelectorAll('.conversation-item').forEach(item => {
            if (item.getAttribute('data-id') === conversationId) {
                item.classList.add('active');
            } else {
                item.classList.remove('active');
            }
        });

        currentConversationId = conversationId;

        // Hiển thị trạng thái loading trong khung chat
        messagesContainer.innerHTML = `
            <div class="empty-docs" style="margin: auto;">
                <div class="typing-indicator" style="scale: 1.5; padding: 20px;">
                    <span class="typing-dot"></span>
                    <span class="typing-dot"></span>
                    <span class="typing-dot"></span>
                </div>
                <p>Đang tải lịch sử hội thoại...</p>
            </div>
        `;
        lucide.createIcons();

        try {
            const response = await fetch(`${API_BASE_URL}/chat/get_conversation/${conversationId}`);
            if (!response.ok) throw new Error('Không thể tải lịch sử tin nhắn');

            const messages = await response.json();
            
            // Dọn sạch khung chat
            messagesContainer.innerHTML = '';

            if (messages.length === 0) {
                resetChatWindow();
                return;
            }

            // Sắp xếp tin nhắn theo created_at tăng dần
            messages.sort((a, b) => new Date(a.created_at) - new Date(b.created_at));

            // Render từng tin nhắn
            messages.forEach(msg => {
                if (msg.role === 'user') {
                    // Render user message
                    const messageDiv = document.createElement('div');
                    messageDiv.className = 'message user-msg';
                    messageDiv.innerHTML = `
                        <div class="message-avatar">
                            <i data-lucide="user"></i>
                        </div>
                        <div class="message-content-wrapper">
                            <div class="message-sender">Bạn</div>
                            <div class="message-content">
                                <p>${escapeHtml(msg.content).replace(/\n/g, '<br>')}</p>
                            </div>
                        </div>
                    `;
                    messagesContainer.appendChild(messageDiv);
                } else {
                    // Render bot message
                    const messageDiv = document.createElement('div');
                    messageDiv.className = 'message system-msg';
                    const botMsgId = 'msg-' + (msg.msg_id || Math.random().toString(36).substring(2, 9));
                    messageDiv.id = botMsgId;
                    
                    messageDiv.innerHTML = `
                        <div class="message-avatar">
                            <i data-lucide="bot"></i>
                        </div>
                        <div class="message-content-wrapper">
                            <div class="message-sender">ChatML Bot</div>
                            <div class="message-content">
                                <!-- Markdown content will be loaded here -->
                            </div>
                        </div>
                    `;
                    messagesContainer.appendChild(messageDiv);
                    
                    // Render content with markdown parsing
                    renderBotResponse(botMsgId, msg.content, msg.sources);
                }
            });

            scrollToBottom();
        } catch (error) {
            console.error('Error loading conversation:', error);
            messagesContainer.innerHTML = `
                <div class="empty-docs" style="margin: auto; color: #ef4444;">
                    <i data-lucide="alert-triangle"></i>
                    <p>Lỗi: ${error.message}</p>
                    <button class="new-chat-btn" style="margin-top: 10px;" id="retryLoadConvBtn">Thử lại</button>
                </div>
            `;
            document.getElementById('retryLoadConvBtn')?.addEventListener('click', () => handleSelectConversation(conversationId));
            lucide.createIcons();
        }
    }

    // Delete Conversation Action
    async function handleDeleteConversation(conversationId) {
        if (!confirm('Bạn có chắc chắn muốn xóa cuộc trò chuyện này? Lịch sử tin nhắn sẽ bị xóa vĩnh viễn.')) {
            return;
        }

        const convItem = document.getElementById(`conv-item-${conversationId}`);
        if (convItem) {
            convItem.style.opacity = '0.5';
            convItem.style.pointerEvents = 'none';
        }

        try {
            const response = await fetch(`${API_BASE_URL}/chat/delete_conversation/${conversationId}`, {
                method: 'DELETE'
            });

            if (!response.ok) throw new Error('Không thể xóa cuộc trò chuyện');

            // Nếu đang xem cuộc trò chuyện bị xóa, dọn dẹp và reset chat window
            if (conversationId === currentConversationId) {
                currentConversationId = null;
                resetChatWindow();
            }

            // Tải lại danh sách
            fetchConversations();
        } catch (error) {
            alert(`Lỗi: ${error.message}`);
            if (convItem) {
                convItem.style.opacity = '1';
                convItem.style.pointerEvents = 'auto';
            }
        }
    }

    // Delete Document Action
    async function handleDeleteDocument(documentId, datasetId, filename) {
        if (!confirm(`Bạn có chắc chắn muốn xóa tài liệu "${filename}" khỏi bộ dữ liệu? Hành động này sẽ xóa toàn bộ vector lưu trữ của tài liệu.`)) {
            return;
        }

        const docItem = document.getElementById(`doc-item-${documentId}`);
        if (docItem) {
            docItem.style.opacity = '0.5';
            docItem.style.pointerEvents = 'none';
        }

        try {
            const response = await fetch(`${API_BASE_URL}/document/document?document_id=${documentId}&dataset_id=${datasetId}`, {
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

    // Create Dataset button listener
    if (createDatasetBtn) {
        createDatasetBtn.addEventListener('click', handleCreateDataset);
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
        const datasetId = uploadDatasetSelect ? uploadDatasetSelect.value : 'null';
        xhr.open('POST', `${API_BASE_URL}/document/upload-document?dataset_id=${datasetId}`, true);

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
                    
                    // Refresh document list and auto-expand the target dataset
                    fetchDocuments().then(() => {
                        const uploadedDsId = result.dataset_id;
                        if (uploadedDsId && uploadedDsId !== 'null') {
                            toggleDataset(uploadedDsId);
                        }
                    });

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
            if (currentConversationId) {
                chatUrl.searchParams.append('conversation_id', currentConversationId);
            }
            const selectedDatasetId = chatDatasetSelect ? chatDatasetSelect.value : 'null';
            chatUrl.searchParams.append('dataset_id', selectedDatasetId);

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

            // 5. Update currentConversationId if we started a new one
            if (!currentConversationId && data.conversation_id) {
                currentConversationId = data.conversation_id;
            }
            // Always refresh conversation list to show newly created chat or update timestamps
            fetchConversations();
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

    // Helper: Get document name asynchronously, utilizing cache
    async function getDocumentName(documentId) {
        if (!documentId) return 'Tài liệu';
        // If it's already cached, return it
        if (documentNameCache[documentId]) {
            return documentNameCache[documentId];
        }
        
        // Fetch from API
        try {
            const response = await fetch(`${API_BASE_URL}/document/get-document/${documentId}`);
            if (response.ok) {
                const data = await response.json();
                if (data.status === 'ok' && data.metadata && data.metadata.filename) {
                    const filename = data.metadata.filename;
                    documentNameCache[documentId] = filename;
                    return filename;
                }
            }
        } catch (error) {
            console.error(`Error fetching document name for ID ${documentId}:`, error);
        }
        
        // If not found or error, fallback to clean name from file path if it looks like one, or the ID
        return getFileName(documentId);
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
                const docId = src.document_id;
                const chunkId = src.chunk_id;
                const key = `${docId}-${chunkId}`;
                if (!seenDocs.has(key)) {
                    seenDocs.add(key);
                    // Use cached name if exists, otherwise fallback to document ID
                    const initialName = documentNameCache[docId] || getFileName(docId);
                    uniqueSources.push({
                        documentId: docId,
                        name: initialName,
                        chunk: chunkId
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
                            <span class="source-badge" data-doc-id="${escapeHtml(src.documentId)}" title="Mã đoạn: ${src.chunk}">
                                <i data-lucide="file-text"></i>
                                <span class="badge-text">${escapeHtml(src.name)}</span>
                            </span>
                        `).join('')}
                    </div>
                `;
                contentDiv.appendChild(sourcesPanel);

                // Fetch document names asynchronously if not already in cache
                const badges = sourcesPanel.querySelectorAll('.source-badge');
                badges.forEach(async badge => {
                    const docId = badge.getAttribute('data-doc-id');
                    if (docId) {
                        const resolvedName = await getDocumentName(docId);
                        const textEl = badge.querySelector('.badge-text');
                        if (textEl) {
                            textEl.textContent = resolvedName;
                        }
                    }
                });
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



    // Create a new Dataset
    async function handleCreateDataset() {
        if (!isServerOnline) return;
        
        const name = prompt('Nhập tên bộ dữ liệu (Dataset) mới:');
        if (name === null) return;
        
        const cleanName = name.trim();
        if (!cleanName) {
            alert('Tên bộ dữ liệu không được để trống!');
            return;
        }

        const desc = prompt('Nhập mô tả cho bộ dữ liệu (tùy chọn):') || '';
        
        try {
            const createResponse = await fetch(`${API_BASE_URL}/document/create-dataset`, {
                method: 'POST'
            });
            if (!createResponse.ok) throw new Error('Không thể tạo bộ dữ liệu');
            const createData = await createResponse.json();
            const datasetId = createData.dataset_id;

            const updateResponse = await fetch(`${API_BASE_URL}/document/update-dataset/${datasetId}?name=${encodeURIComponent(cleanName)}&description=${encodeURIComponent(desc)}`, {
                method: 'POST'
            });
            if (!updateResponse.ok) throw new Error('Không thể đặt tên bộ dữ liệu');

            await fetchDocuments();
            if (uploadDatasetSelect) {
                uploadDatasetSelect.value = datasetId;
            }
        } catch (error) {
            alert(`Lỗi tạo bộ dữ liệu: ${error.message}`);
        }
    }

    // Rename an existing Dataset
    async function handleRenameDataset(datasetId, currentName) {
        const newName = prompt('Nhập tên mới cho bộ dữ liệu:', currentName);
        if (newName === null) return;
        
        const cleanName = newName.trim();
        if (!cleanName) {
            alert('Tên bộ dữ liệu không được để trống!');
            return;
        }

        try {
            const response = await fetch(`${API_BASE_URL}/document/update-dataset/${datasetId}?name=${encodeURIComponent(cleanName)}`, {
                method: 'POST'
            });
            if (!response.ok) throw new Error('Không thể đổi tên bộ dữ liệu');
            fetchDocuments();
        } catch (error) {
            alert(`Lỗi đổi tên: ${error.message}`);
        }
    }

    // Delete a Dataset and all its documents
    async function handleDeleteDataset(datasetId, name) {
        if (!confirm(`Bạn có chắc chắn muốn xóa bộ dữ liệu "${name}"? Hành động này sẽ xóa tất cả tài liệu bên trong và toàn bộ vector lưu trữ.`)) {
            return;
        }

        const datasetItem = document.getElementById(`dataset-item-${datasetId}`);
        if (datasetItem) {
            datasetItem.style.opacity = '0.5';
            datasetItem.style.pointerEvents = 'none';
        }

        try {
            const response = await fetch(`${API_BASE_URL}/document/dataset/${datasetId}`, {
                method: 'DELETE'
            });
            if (!response.ok) throw new Error('Không thể xóa bộ dữ liệu');
            fetchDocuments();
        } catch (error) {
            alert(`Lỗi: ${error.message}`);
            if (datasetItem) {
                datasetItem.style.opacity = '1';
                datasetItem.style.pointerEvents = 'auto';
            }
        }
    }

    // Global toggle helper for accordions (loads documents dynamically on demand)
    window.toggleDataset = async function(datasetId) {
        const docContainer = document.getElementById(`dataset-docs-${datasetId}`);
        const itemContainer = document.getElementById(`dataset-item-${datasetId}`);
        if (!docContainer || !itemContainer) return;

        const isCollapsed = docContainer.classList.contains('collapsed');
        
        // If expanding and documents are not yet loaded, fetch them
        if (isCollapsed && docContainer.getAttribute('data-loaded') === 'false') {
            docContainer.innerHTML = `
                <div class="empty-docs" style="padding: 10px 0; opacity: 0.6; font-size: 0.7rem; display: flex; align-items: center; justify-content: center; gap: 6px;">
                    <div class="typing-indicator" style="scale: 0.8; padding: 0; display: inline-flex;">
                        <span class="typing-dot" style="background-color: var(--accent-secondary);"></span>
                        <span class="typing-dot" style="background-color: var(--accent-secondary);"></span>
                        <span class="typing-dot" style="background-color: var(--accent-secondary);"></span>
                    </div>
                    <span>Đang tải...</span>
                </div>
            `;
            
            try {
                const response = await fetch(`${API_BASE_URL}/document/document-by-dataset/${datasetId}`);
                if (!response.ok) throw new Error('Không thể tải tài liệu');
                const docs = await response.json() || [];

                if (docs.length === 0) {
                    docContainer.innerHTML = `<div class="empty-docs" style="padding: 10px 0; opacity: 0.6; font-size: 0.7rem;"><p>Không có tài liệu nào</p></div>`;
                } else {
                    docContainer.innerHTML = docs.map(doc => {
                        const docId = doc._id;
                        const filename = doc.filename;
                        const size = doc.file_size_byte ? formatBytes(doc.file_size_byte) : '';
                        const fileType = filename.split('.').pop().toLowerCase();
                        
                        let iconName = 'file-text';
                        if (fileType === 'pdf') iconName = 'file-text';
                        else if (fileType === 'docx') iconName = 'file-type-2';
                        else if (fileType === 'txt') iconName = 'file-code';
                        else if (fileType === 'md') iconName = 'file-edit';

                        // Save document name in cache
                        documentNameCache[docId] = filename;

                        return `
                            <div class="dataset-doc-item" id="doc-item-${docId}">
                                <div class="dataset-doc-info">
                                    <i data-lucide="${iconName}" class="dataset-doc-icon"></i>
                                    <span class="dataset-doc-name" title="${escapeHtml(filename)}">
                                        ${escapeHtml(filename)}
                                        ${size ? `<span class="dataset-doc-meta">${size}</span>` : ''}
                                    </span>
                                </div>
                                <button class="dataset-doc-action-btn delete-doc-btn" data-id="${docId}" data-dataset-id="${datasetId}" data-name="${escapeHtml(filename)}" title="Xóa tài liệu">
                                    <i data-lucide="trash-2" style="width: 12px; height: 12px;"></i>
                                </button>
                            </div>
                        `;
                    }).join('');

                    // Add Delete Document event listeners for newly loaded buttons
                    docContainer.querySelectorAll('.delete-doc-btn').forEach(btn => {
                        btn.addEventListener('click', (e) => {
                            e.stopPropagation();
                            const id = btn.getAttribute('data-id');
                            const dsId = btn.getAttribute('data-dataset-id');
                            const name = btn.getAttribute('data-name');
                            handleDeleteDocument(id, dsId, name);
                        });
                    });
                }
                
                docContainer.setAttribute('data-loaded', 'true');
            } catch (error) {
                console.error(`Error loading documents for dataset ${datasetId}:`, error);
                docContainer.innerHTML = `<div class="empty-docs" style="padding: 10px 0; color: #ef4444; font-size: 0.7rem;"><p>Lỗi tải tài liệu</p></div>`;
            }
        }
        
        docContainer.classList.toggle('collapsed');
        itemContainer.classList.toggle('expanded');
        lucide.createIcons();
    };
});
