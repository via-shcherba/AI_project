console.log('*** CHAT JS VERSION 2.6.4')
const MAX_RESPOND_WAITING_TIME = 60000; 
let maxRequestQueue = 5;
let isCloseConversationBtnBlocked = false;
let websocketPingInterval;
let chatSocket;

const userId = JSON.parse(document.getElementById('session_id').textContent);

function connectToRoom() {
    const params = new URLSearchParams(window.location.search);
    const convertedParams = convertJsonStringToObject(params.get('params'));
    if (convertedParams?.is_local === true) {
        chatSocket = new WebSocket(`ws://${window.location.host}/ws/chat/${userId}/`);
    } else {
        chatSocket = new WebSocket(`wss://${window.location.host}/wss/chat/${userId}/`);
    }    
}

let isAttachmentLoader = false;
let isUnreadResponses = false;
let isGettingHistory = false;
let scrollNotInDown = false;
let isIntentModel = false;
let isLoading = false;
let isTyping = false;

let restartCommandForParent = '';
let unreadMessagesCounter = 0;
let systemMessages = {};
let attachedFiles = [];
let negativeCounter = 0;
let windowWidth = 0;
let waitingTimeout;
let respondent;
let chatType;

connectToRoom();

const chatContainer = document.querySelector('.chat-container');
const topMenuButton = document.getElementById('dropdown-button');
const messagesList = document.querySelector('.messages-list');
const messageForm = document.querySelector('.message-form');
const textarea = document.querySelector('.main-textarea');
const submitButton = document.getElementById('submit');
const messagesBox = document.getElementById('messagesBox');
const scrollDownButton = document.getElementById('scrollDownButton');
const unreadIndicator = document.getElementById('unread-ind');
const overlay = document.getElementById('overlay');
const menu = document.getElementById('top-dropdown-menu');
const closeConversationBtn = document.getElementById('close-conversation');
const maximizeBtn = document.getElementById('maximize-chat-btn');
const normalizeBtn = document.getElementById('normalize-chat-btn');
const chatName = document.getElementById('chat-name');
const fileUpload = document.getElementById('file-upload');
const topSpinner = document.getElementById('top-spinner');
const attachmentsBox = document.getElementById('attachments-box');
const attachmentsList = document.getElementById('attachments-list');
const warningBlock = document.getElementById('warning');
const attachmentWarningMessage = document.getElementById('attachment-warning-message');
const attachmentLoader = document.getElementById('attachment-loader');

//Listen messages from parent
window.addEventListener('message', function(event) {    
    reconnect();
    if (event.data?.type === 'user_data') {
        send(event.data); 
    }
    if (event.data?.screen_size === 'mobile') {
        if (messagesList) {
            //specially for mobile version to prevent interaction with the main page
            messagesList.style.paddingTop = '95%';
        }
    }
    if (event.data?.screen_size === 'desktop') {
        if (messagesList) {
            messagesList.style.paddingTop = '0';
        }
    }
    // To recieve post message about authorization
    if (event.data?.type === 'restart') {
        restartCommandForParent = event.data
        sendToParent(event.data)
    }
    // Only for login or logout this command
    if (event.data?.type === 'restart_backend') {
        send({'type': 'command', 'message': 'restart_backend'});
    }
    // To setup interface translations
    if (event.data?.type === 'interface') {
        sendToParent(event.data)
    }
});    

showTopSpinner('Loading...');
textarea.focus();
textarea.setAttribute('disabled', 'disabled');

function showChatName(name) {
    topSpinner.classList.add('hidden');
    chatName.innerHTML = name
}

chatSocket.onopen = function() {
    sendToParent({'type' : 'connect'})
    // Ping generator for sebsoket
    if (!websocketPingInterval) {
        websocketPingInterval = setInterval(() => {
            send({'type': 'ping'});
        }, 30000);
    }
}

chatSocket.onmessage = function(e) {
    const data = JSON.parse(e.data);   
    for (const dataRow of data) {
        readRecievedData(dataRow)
    }
}

chatSocket.onclose = function(e) {
    sendToParent({'type' : 'disconnect'})
    clearInterval(websocketPingInterval);
    reconnect();
}

chatSocket.onerror = function(e) {
    menu.classList.add('hidden');
    hideTypingIndicator();
    isLoading = false;
    clearInterval(websocketPingInterval);
}

function readRecievedData(data) {
    switch(data?.type) {
        case 'connection_established': 
            //sendToParent({'type' : 'user_data_request'});
            isGettingHistory = true;
            break;
        case 'empty_story':
            showConnectionDate(false, null);
            sendToParent({'type' : 'unread_messages_indicator', 'message' : 0});
            break;
        case 'connection_date':
            showConnectionDate(true, data.message);
            break;
        case 'join':           
            respondent = data;
            joinOrLeftSender(data, true)
            runWithDelay(showChatName, 200, respondent.name)   
            disableTextareaForBotRequests();    
            scrollToBottom();
            break;
        case 'bot_version':
            console.log('*** CHAT BOT VERSION: ' + data?.message);
            break;
        case 'translation_dictionary':
            if (typeof data?.system_messages === 'string') {
                systemMessages = convertJsonStringToObject(data?.system_messages);
            } else {
                systemMessages = data?.system_messages;
            }
            changeTitles();
            break;
        case 'left':            
            joinOrLeftSender(data, false)
            runWithDelay(showChatName, 200, '')   
            hideTypingIndicator();   
            scrollToBottom();
            textarea.setAttribute('disabled', 'disabled');
            break;
        case 'greetings':            
            showGreetings(data)
            textarea.removeAttribute('disabled');
            break;
        case 'chat_type':           
            chatType = data?.message;
            if (data?.respondent) {
                respondent = data.respondent
            }
            break;
        case 'command': 
            if (data.message === 'show_typing_indicator' && data?.name) {  
                if (chatType === 'bot') {
                    isLoading = true;
                }   
                showTypingIndicator(data);
                checkScroll();
                if (scrollNotInDown) {   
                    showSideTypingIndicator();
                }                 
                if (data?.scroll === 'True') {                    
                    scrollToBottom()
                    scrollNotInDown = true;
                };                             
            } else if (data.message === 'hide_typing_indicator') {
                hideTypingIndicator();           
            } else if (data.message === 'show_top_spinner') {
                runWithDelay(showTopSpinner, 200, data?.text)   
                scrollToBottom();
            } else if (data.message === 'hide_top_spinner') {
                topSpinner.classList.add('hidden');
                textarea.removeAttribute('disabled');
                scrollToBottom();
            } else if (data.message ==='hide_file_spinner') {
                const fileSpinner = document.getElementById(data.id);
                if (fileSpinner) fileSpinner.classList.add('hidden');
                const fileMetadata = document.getElementById(data.id + 'md');
                if (fileMetadata) {
                    fileMetadata.innerHTML = systemMessages?.SENT_MSG + data.sent_time;
                    scrollToBottom();
                }
            } else if (data.message ==='show_attachment_loader') {
                isAttachmentLoader = true;
                attachmentLoader.classList.remove('hidden')
            } else if (data.message ==='hide_attachment_loader') {
                isAttachmentLoader = false;
                attachmentLoader.classList.add('hidden')
            } else if (data.message ==='show_top_menu') {
                topMenuButton.classList.remove('hidden');
            } else if (data.message ==='offer_call_agent') {
                isIntentModel = true;
            } else if (data.message ==='collapse_widget') {
                closeWidget();
            } else if (data.message ==='disable_widget') {
                showTopSpinner(systemMessages?.SERVICE_IN_PROGRESS_MSG);
                textarea.setAttribute('disabled', 'disabled');
            } else if (data.message ==='control') {
                isGettingHistory = false;
                changeTitles();
                runWithDelay(scrollToBottom, 0, true);
                if (findRepetitiveElements(messagesList.children, 'sent').length > 0 && chatType === 'bot') {
                    showSystemMessage(systemMessages?.CONNECTION_ERROR_MSG, null);
                }
                removeShowCallAgentOffer();
            } else if (data.message === 'reload_shell_js') {
                sendToParent({'type': 'command', 'message': 'reload_shell_js'});
            } else if (data.message === 'restart_frontend') {
                restartCommandForParent.type = 'restart_frontend';
                sendToParent(restartCommandForParent);
            }
            break;
        case 'message':  
            checkScroll();
            const is_unread = data?.is_unread === 'True' ? true : false
            if (scrollNotInDown) {
                scrollDownButton.classList.remove('hidden');
                unreadIndicator.classList.remove('hidden');        
                isUnreadResponses = true;
                if (!is_unread) {
                    unreadMessagesCounter += 1;
                }              
                showRecievedMessage(data, data?.like, true);
                showUnreadCounter();
            } else {
                unreadMessagesCounter = 0;
                showRecievedMessage(data, data?.like, false);
            }
            isLoading = false;
            textarea.removeAttribute('disabled');
            topSpinner.classList.add('hidden');
            stopResponseWaitingTimeout();           
                                  
            if (unreadMessagesCounter > 0 && !isGettingHistory && !is_unread) {
                sendToParent({'type' : 'unread_messages_indicator', 'message' : unreadMessagesCounter});
            }         
            break;
        case 'system_message':
            showSystemMessage(data?.message, data?.user_time);
            isLoading = false;
            textarea.removeAttribute('disabled');
            break;
        case 'attachment':
            showAttachment(data, true);
            topSpinner.classList.add('hidden');
            break;
        case 'file':
            showRecievedFile(data);
            topSpinner.classList.add('hidden');
            break;
        case 'request':            
            showRequest(data, true);
            break;
        case 'unread_messages_counter': 
            const counter = data?.message == null ? 0 : Number(data.message);
            sendToParent({'type' : 'unread_messages_indicator', 'message' : counter})
            break;
    }  
}

function negativeSummarizer(indicator) {
    if (indicator === 'True' && !isGettingHistory) {
        negativeCounter ++;
    } else {
        negativeCounter = 0;
    }
    if (negativeCounter >= 2) {
        showCallAgentOffer();
        negativeCounter = 0;
    } 
}

function disableTextareaForBotRequests() {
    if (chatType === 'bot') {
        textarea.setAttribute('disabled', 'disabled');
    }
}

function stopResponseWaitingTimeout() {
    if (waitingTimeout) {
        clearTimeout(waitingTimeout);
        waitingTimeout = null;
    }
}

function showTopSpinner(message) {  
    showChatName('')
    if (message) {
        const topSpinnerMessage = document.getElementById('top-spinner-message');
        topSpinnerMessage.innerHTML = message;
    }   
    topSpinner.classList.remove('hidden');
}

function changeTitles() {
    if (systemMessages?.TYPE_Y_MSG) {
        textarea.placeholder = systemMessages.TYPE_Y_MSG
    }
    if (chatType === 'bot' && systemMessages?.BOT_NAME) {
        runWithDelay(showChatName, 200, systemMessages.BOT_NAME);
    }
}

messageForm.addEventListener('submit', (event) => {
    if (chatType === 'bot') isLoading = true;

    event.preventDefault();

    textarea.rows = 1;      
    const message = truncateString(textarea.value.trim());

    if (message.length === 0 && attachedFiles.length === 0) {
        return;
    }

    if (message.length > 0) {
        showRequest(message, false);
    }
    
    if (attachedFiles.length > 0) {
        attachedFiles.forEach(file => {
            showAttachment(file, false);
        });  
        attachmentsList.innerHTML = '';
        attachedFiles = [];
    }
        
    textarea.value = '';       
    submitButton.setAttribute('disabled', true);   
    removeShowCallAgentOffer();
});

function showMaximazeBtn() {
    maximizeBtn.classList.add('hidden');
    normalizeBtn.classList.remove('hidden');
}

function showNormalizeBtn() {
    normalizeBtn.classList.add('hidden');
    maximizeBtn.classList.remove('hidden');
}

window.addEventListener('resize', handleWindowSize);

function handleWindowSize() {
    windowWidth = window.innerWidth;   
    if (windowWidth !== null) {
        const messageText = document.querySelectorAll('[id=message-text]');       
        if (messageText) {
            if (windowWidth > 344 || windowWidth < 344) {
                for (let i=0; i < messageText.length; i++) {
                    messageText[i].classList.add('max-width');
                    messageText[i].classList.remove('normal-width');
                }
            } else {
                for (let i=0; i < messageText.length; i++) {
                    messageText[i].classList.add('normal-width');
                    messageText[i].classList.remove('max-width');
                }
            }
        }       
    }
}

function createRequestHTML(request, userTime) {
    const metadata = systemMessages?.SENT_MSG + userTime;
    return `
    <div id="message-text" class="message-text">
        <div>
            <div class="message-block">
                <div class="message-field">      
                    ${request}
                </div>
                <div class="message-metadata">${metadata}</div>
            </div>  
        </div> 
    </div>
    `;
}

function showRequest(message, isOut) {
    const messageItem = document.createElement('li');
    messageItem.classList.add('sent');
    let userTime = getCurrentDateTime();
    let request = message;
    if (isOut) {
        userTime = message.user_time;      
        request = message.request;
    } else {            
        chatSocket.send(JSON.stringify({
            'type': 'request',
            'uuid': generateUUID(),
            'name' : 'user',
            'request' : message,
            'user_time' : userTime
        }));
        if (chatType === 'bot') {
            startResponseWaitingTimeout()
        }
    }
    messageItem.innerHTML = createRequestHTML(request, userTime);
    if (chatType !== 'bot') {
        joinRequests(messagesList, messageItem, request, userTime);
    } else {
        messagesList.appendChild(messageItem);
        isLoading = false;
        if (!isOut) {
            isLoading = true;
            const sender = {
                name : systemMessages.BOT_NAME,
                avatar : respondent?.avatar
            }
            showTypingIndicator(sender);
        }  
    }
    handleWindowSize();
    scrollToBottom();    
}

function joinRequests(messagesList, messageItem, message, userTime) {
    const repetitiveRequests = getAllRepetitiveRequests(messagesList.children)
    if (repetitiveRequests.length > 0) {
        repetitiveRequests.forEach(request => {
            messagesList.removeChild(request);
        });
        repetitiveRequests.forEach(request => {
            const messageField = request.querySelector('.message-field');
            if (messageField) {
                const requestHTML = messageField.innerHTML;    
                const liElement = document.createElement('li');
                liElement.classList.add('part-message-sent');    
                liElement.innerHTML = `<div><div class="message-field message-part-text">${requestHTML}</div></div>`;   
                messagesList.appendChild(liElement);       
            }
        });
        messageItem.innerHTML = createRequestHTML(message, userTime);
        messagesList.appendChild(messageItem);
    } else {
        messagesList.appendChild(messageItem);
    }
}

function startResponseWaitingTimeout() {
    if (waitingTimeout) {
        clearTimeout(waitingTimeout);
    }

    waitingTimeout = setTimeout(() => {
        const errorMessage = systemMessages?.CONNECTION_ERROR_MSG ? systemMessages?.CONNECTION_ERROR_MSG : 'Error';
        showSystemMessage(errorMessage, null);
        isLoading = false;
        waitingTimeout = null; 
    }, MAX_RESPOND_WAITING_TIME);
}

function addAttachmentPill(file) {
    attachmentsBox.classList.remove('hidden');
    const attachmentItem = document.createElement('li');
    attachmentItem.setAttribute('id', file.id)
    attachmentItem.innerHTML = `
        <div class="pill">
          <span class="icon">
            ${file.file_type === 'pdf' ? `
             <svg focusable="false" aria-hidden="true" viewBox="0 0 560 640" part="icon" data-key="pdf">
              <g>
                <path fill="#8e030f" d="M51 0A51 51 0 000 51v538c0 28 23 51 51 51h458c28 0 51-23 51-51V203L371 0z"></path>
                <path fill="#640103" d="M560 204v10H432s-63-13-61-67c0 0 2 57 60 57z"></path>
                <path fill="#feb8ab" d="M371 0v146c0 17 11 58 61 58h128z"></path>
                <path fill="#fff" d="M149 490h-33v41c0 4-3 7-8 7-4 0-7-3-7-7V429c0-6 5-11 11-11h37c24 0 38 17 38 36 0 20-14 36-38 36zm-1-59h-32v46h32c14 0 24-9 24-23s-10-23-24-23zm104 107h-30c-6 0-11-5-11-11v-98c0-6 5-11 11-11h30c37 0 62 26 62 60s-24 60-62 60zm0-107h-26v93h26c29 0 46-21 46-47 1-25-16-46-46-46zm163 0h-58v39h57c4 0 6 3 6 7s-3 6-6 6h-57v48c0 4-3 7-8 7-4 0-7-3-7-7V429c0-6 5-11 11-11h62c4 0 6 3 6 7 1 3-2 6-6 6z"></path>
              </g>
             </svg>
             ` : `
              <svg focusable="false" aria-hidden="true" viewBox="0 0 5600 6400" part="icon" data-key="image">
                <g>
                    <path fill="#06a59a" d="M513 4A507 507 0 005 512v5384c0 280 227 507 508 507h4577c280 0 507-227 507-507V2035L3707 4H512z"></path>
                    <path fill="#056764" d="M5598 2035v100H4318s-631-126-613-671c0 1 21 571 600 571z"></path>
                    <path fill="#acf3e4" d="M3707 0v1456c0 166 111 579 611 579h1280z"></path>
                    <path fill="#fff" d="M1012 5374V3283h2091v2091zm1880-1884H1223v1260h1669zm-959 838l391-526 121 213 140-44 98 563H1375l349-332zm-385-364c-91 0-165-69-165-154s74-154 165-154 165 69 165 154-74 154-165 154z"></path>
                </g>
              </svg>`
            }    
          </span>
          <span class="attachment-name" title="${file.name}">${file.name}</span>
          <span class="remove-attachment" title="${systemMessages?.DO_NOT_SEND_FILE_MSG} ${file.name}" onclick="removeAttachment('${file.id}')">
            <svg focusable="false" aria-hidden="true" viewBox="0 0 520 520" part="icon" data-key="close">
              <g>
                <path d="M310 254l130-131c6-6 6-15 0-21l-20-21c-6-6-15-6-21 0L268 212a10 10 0 01-14 0L123 80c-6-6-15-6-21 0l-21 21c-6 6-6 15 0 21l131 131c4 4 4 10 0 14L80 399c-6 6-6 15 0 21l21 21c6 6 15 6 21 0l131-131a10 10 0 0114 0l131 131c6 6 15 6 21 0l21-21c6-6 6-15 0-21L310 268a10 10 0 010-14z"></path>
              </g>
            </svg>
          </span>
        </div>
    `;
    attachmentsList.appendChild(attachmentItem);
    scrollToBottom();
}

function showAttachment(file, isOut) {
    if (!isOut) {
        send({
            'type': 'attachment',
            'id': file.id,
            'file_id': file.file_id,
            'name': file.name,
            'file_type' : file.file_type,
            'data' : file.data        
        });
        file.data = null;
    }
    const attachmentItem = document.createElement('li');
    attachmentItem.classList.add('attachment-sent');
    const sent_time = file?.sent_time ? systemMessages?.SENT_MSG + file.sent_time : '';
    attachmentItem.innerHTML = `
    <div class="message-block">
        <div class="attachment-view">
            <div class="main-attachment-icon">  
              ${file.file_type === 'pdf' ? 
              `<svg focusable="false" aria-hidden="true" viewBox="0 0 560 640" part="icon" data-key="pdf">
                <g>
                  <path fill="#8e030f" d="M51 0A51 51 0 000 51v538c0 28 23 51 51 51h458c28 0 51-23 51-51V203L371 0z"></path>
                  <path fill="#640103" d="M560 204v10H432s-63-13-61-67c0 0 2 57 60 57z"></path>
                  <path fill="#feb8ab" d="M371 0v146c0 17 11 58 61 58h128z"></path>
                  <path fill="#fff" d="M149 490h-33v41c0 4-3 7-8 7-4 0-7-3-7-7V429c0-6 5-11 11-11h37c24 0 38 17 38 36 0 20-14 36-38 36zm-1-59h-32v46h32c14 0 24-9 24-23s-10-23-24-23zm104 107h-30c-6 0-11-5-11-11v-98c0-6 5-11 11-11h30c37 0 62 26 62 60s-24 60-62 60zm0-107h-26v93h26c29 0 46-21 46-47 1-25-16-46-46-46zm163 0h-58v39h57c4 0 6 3 6 7s-3 6-6 6h-57v48c0 4-3 7-8 7-4 0-7-3-7-7V429c0-6 5-11 11-11h62c4 0 6 3 6 7 1 3-2 6-6 6z"></path>
                </g>
              </svg>` :
              `
              <svg focusable="false" aria-hidden="true" viewBox="0 0 5600 6400" part="icon" data-key="image">
                <g>
                  <path fill="#06a59a" d="M513 4A507 507 0 005 512v5384c0 280 227 507 508 507h4577c280 0 507-227 507-507V2035L3707 4H512z"></path>
                  <path fill="#056764" d="M5598 2035v100H4318s-631-126-613-671c0 1 21 571 600 571z"></path>
                  <path fill="#acf3e4" d="M3707 0v1456c0 166 111 579 611 579h1280z"></path>
                  <path fill="#fff" d="M1012 5374V3283h2091v2091zm1880-1884H1223v1260h1669zm-959 838l391-526 121 213 140-44 98 563H1375l349-332zm-385-364c-91 0-165-69-165-154s74-154 165-154 165 69 165 154-74 154-165 154z"></path>
                </g>
              </svg> ` }
              ${!isOut ? `
              <div id="${file.id}" class="file-spinner-container">
                <div class="file-spinner"></div>
              </div>` : `
              `}            
            </div> 
            <div class="attachment-message-footer">   
            ${file.file_type === 'pdf' ?
              `<svg focusable="false" aria-hidden="true" viewBox="0 0 560 640" part="icon" data-key="pdf">
                <g>
                  <path fill="#8e030f" d="M51 0A51 51 0 000 51v538c0 28 23 51 51 51h458c28 0 51-23 51-51V203L371 0z"></path>
                  <path fill="#640103" d="M560 204v10H432s-63-13-61-67c0 0 2 57 60 57z"></path>
                  <path fill="#feb8ab" d="M371 0v146c0 17 11 58 61 58h128z"></path>
                  <path fill="#fff" d="M149 490h-33v41c0 4-3 7-8 7-4 0-7-3-7-7V429c0-6 5-11 11-11h37c24 0 38 17 38 36 0 20-14 36-38 36zm-1-59h-32v46h32c14 0 24-9 24-23s-10-23-24-23zm104 107h-30c-6 0-11-5-11-11v-98c0-6 5-11 11-11h30c37 0 62 26 62 60s-24 60-62 60zm0-107h-26v93h26c29 0 46-21 46-47 1-25-16-46-46-46zm163 0h-58v39h57c4 0 6 3 6 7s-3 6-6 6h-57v48c0 4-3 7-8 7-4 0-7-3-7-7V429c0-6 5-11 11-11h62c4 0 6 3 6 7 1 3-2 6-6 6z"></path>
                </g>
              </svg>` :
              `
              <svg focusable="false" aria-hidden="true" viewBox="0 0 5600 6400" part="icon" data-key="image">
                <g>
                  <path fill="#06a59a" d="M513 4A507 507 0 005 512v5384c0 280 227 507 508 507h4577c280 0 507-227 507-507V2035L3707 4H512z"></path>
                  <path fill="#056764" d="M5598 2035v100H4318s-631-126-613-671c0 1 21 571 600 571z"></path>
                  <path fill="#acf3e4" d="M3707 0v1456c0 166 111 579 611 579h1280z"></path>
                  <path fill="#fff" d="M1012 5374V3283h2091v2091zm1880-1884H1223v1260h1669zm-959 838l391-526 121 213 140-44 98 563H1375l349-332zm-385-364c-91 0-165-69-165-154s74-154 165-154 165 69 165 154-74 154-165 154z"></path>
                </g>
              </svg> `}  
              <div class="text" title="${file.name}">${file.name}</div>
            </div>
        </div>
        <div id="${file.id}md" class="message-metadata">${sent_time}</dv>
    </div>
    `;
    messagesList.appendChild(attachmentItem);
    isLoading = false;
    scrollToBottom();
    attachmentsBox.classList.add('hidden');
}

function showConnectionDate(isOut, text) {
    const messageItem = document.createElement('li');
    const currentTime = getCurrentDateTime();
    let message = systemMessages?.TODAY_MSG + ' ' + currentTime;
    if (isOut) {
        message = text;
    } else {
        chatSocket.send(JSON.stringify({
            'type': 'connection_date',
            'message': message,
            'user_id': userId,
            'user_time' : currentTime
        }));
    }     
    messageItem.innerHTML = `
        <div class="embedded-messaging-timestamp">
            <span id="current-time" class="message-text-date">${message}</span>         
        </div>
    `;
    messagesList.appendChild(messageItem);
}

function showSystemMessage(text, user_time) {
    const messageItem = document.createElement('li');   
    const dateTime = user_time ? user_time : getCurrentDateTime();
    messageItem.innerHTML = `
        <div class="embedded-messaging-timestamp">
            <span id="current-time" class="message-text-date">${text} ${dateTime}</span>         
        </div>
    `;
    messagesList.appendChild(messageItem);
    hideTypingIndicator();
    setTimeout(() => {
        scrollToBottom();
    }, 500); 
}

function showRecievedFile(sender) {
    const fileName = sender.response.name;
    const mimeType = sender.response.mimeType;
    const type = mimeType.split('/')[1];
    sender.response = `
        <div class="recieved-attachment">        
            ${type === 'pdf' ? `
            <div class="pdf-icon">
                <svg focusable="false" aria-hidden="true" viewBox="0 0 560 640" part="icon" data-key="pdf">
                    <g>
                        <path fill="#8e030f" d="M51 0A51 51 0 000 51v538c0 28 23 51 51 51h458c28 0 51-23 51-51V203L371 0z"></path>
                        <path fill="#640103" d="M560 204v10H432s-63-13-61-67c0 0 2 57 60 57z"></path>
                        <path fill="#feb8ab" d="M371 0v146c0 17 11 58 61 58h128z"></path>
                        <path fill="#fff" d="M149 490h-33v41c0 4-3 7-8 7-4 0-7-3-7-7V429c0-6 5-11 11-11h37c24 0 38 17 38 36 0 20-14 36-38 36zm-1-59h-32v46h32c14 0 24-9 24-23s-10-23-24-23zm104 107h-30c-6 0-11-5-11-11v-98c0-6 5-11 11-11h30c37 0 62 26 62 60s-24 60-62 60zm0-107h-26v93h26c29 0 46-21 46-47 1-25-16-46-46-46zm163 0h-58v39h57c4 0 6 3 6 7s-3 6-6 6h-57v48c0 4-3 7-8 7-4 0-7-3-7-7V429c0-6 5-11 11-11h62c4 0 6 3 6 7 1 3-2 6-6 6z"></path>
                    </g>
                </svg>
            </div>` : `
            <div class="preview-container">
                <img class="preview-region" src="${sender.response.url}">
            </div>`
            }      
            <div class="attachment-message-footer">
                ${type === 'pdf' ?
                    `<svg focusable="false" aria-hidden="true" viewBox="0 0 560 640" part="icon" data-key="pdf">
                        <g>
                            <path fill="#8e030f" d="M51 0A51 51 0 000 51v538c0 28 23 51 51 51h458c28 0 51-23 51-51V203L371 0z"></path>
                            <path fill="#640103" d="M560 204v10H432s-63-13-61-67c0 0 2 57 60 57z"></path>
                            <path fill="#feb8ab" d="M371 0v146c0 17 11 58 61 58h128z"></path>
                            <path fill="#fff" d="M149 490h-33v41c0 4-3 7-8 7-4 0-7-3-7-7V429c0-6 5-11 11-11h37c24 0 38 17 38 36 0 20-14 36-38 36zm-1-59h-32v46h32c14 0 24-9 24-23s-10-23-24-23zm104 107h-30c-6 0-11-5-11-11v-98c0-6 5-11 11-11h30c37 0 62 26 62 60s-24 60-62 60zm0-107h-26v93h26c29 0 46-21 46-47 1-25-16-46-46-46zm163 0h-58v39h57c4 0 6 3 6 7s-3 6-6 6h-57v48c0 4-3 7-8 7-4 0-7-3-7-7V429c0-6 5-11 11-11h62c4 0 6 3 6 7 1 3-2 6-6 6z"></path>
                        </g>
                    </svg>  ` : `
                    <svg focusable="false" aria-hidden="true" viewBox="0 0 5600 6400" part="icon" data-key="image">
                        <g>
                            <path fill="#06a59a" d="M513 4A507 507 0 005 512v5384c0 280 227 507 508 507h4577c280 0 507-227 507-507V2035L3707 4H512z"></path>
                            <path fill="#056764" d="M5598 2035v100H4318s-631-126-613-671c0 1 21 571 600 571z"></path>
                            <path fill="#acf3e4" d="M3707 0v1456c0 166 111 579 611 579h1280z"></path>
                            <path fill="#fff" d="M1012 5374V3283h2091v2091zm1880-1884H1223v1260h1669zm-959 838l391-526 121 213 140-44 98 563H1375l349-332zm-385-364c-91 0-165-69-165-154s74-154 165-154 165 69 165 154-74 154-165 154z"></path>
                        </g>
                    </svg>`
                }

                <div class="text" title="${fileName}">${fileName}</div>` +
                // <a class="download" title="${systemMessages?.DOWNLOAD_MSG}" onclick="downloadFile('${sender.response.url}','${fileName}')">
                //     <svg focusable="false" aria-hidden="true" viewBox="0 0 520 520" part="icon" data-key="download">
                //         <g>
                //         <path d="M485 310h-30c-8 0-15 7-15 15v100c0 8-7 15-15 15H95c-8 0-15-7-15-15V325c0-8-7-15-15-15H35c-8 0-15 7-15 15v135a40 40 0 0040 40h400a40 40 0 0040-40V325c0-8-7-15-15-15zm-235 66c6 6 15 6 21 0l135-135c6-6 6-15 0-21l-21-21c-6-6-15-6-21 0l-56 56c-6 6-17 2-17-7V35c-1-8-9-15-16-15h-30c-8 0-15 7-15 15v212c0 9-11 13-17 7l-56-56c-6-6-15-6-21 0l-21 22c-6 6-6 15 0 21z"></path>
                //         </g>
                //     </svg>
                // </a>
            `</div>
        </div>
    `;
    showRecievedMessage(sender, false, false);
    scrollToBottom();
}

function createRecievedHTML(sender, like) {
    //Don't show like/dislike buttons if response less than 140 symbols
    let hiddenClass = sender.response.length > 140 ? '' : 'hidden';
    hiddenClass = like === 'True' ? hiddenClass : 'hidden'
    const likeActive = sender?.grade === 'like' ? 'active' : ''
    const dislikeActive = sender?.grade === 'dislike' ? 'active' : ''
    return `
    <div id="message-text" class="message-text">           
        <div class="sender-icon">
            ${sender.avatar !== '' ? `<img src="${sender.avatar}" alt="${sender?.name}" title="${sender?.name}">` : `<div class="default-icon">${getInitials(sender?.name)}</div>`}    
        </div>           
        <div>
            <div class="message-block">
                <div class="message-field">
                    <div>
                        ${sender?.response}
                        ${sender?.disclaimer && sender?.disclaimer !== '' ? `<br><span class="disclaimer">${sender.disclaimer}</span>` : ``}
                    </div>
                    <div id="${sender?.uuid}" class="evaluatine-button-container ${hiddenClass}">
                        <div onclick="setLike('${sender.uuid}');" title="${systemMessages?.LIKE_MSG}" class="icon-button like ${likeActive}">
                            <div>
                                <svg width="16" height="16" viewBox="0 0 16 16" xmlns="http://www.w3.org/2000/svg">
                                    <path d="M5.45573 7.04203L8.04088 3.17505C8.29309 2.79469 8.92362 2.54112 9.42805 2.7313C9.99552 2.92148 10.3738 3.55541 10.2477 4.12595L9.93247 6.15453C9.86942 6.59829 10.1847 6.91525 10.563 6.91525H13.0851C14.0309 6.91525 14.6111 7.64427 14.2831 8.56347C13.9553 9.48267 13.6653 11.1309 12.7699 12.5572C12.3601 13.2099 11.9108 13.6666 11.1432 13.6666C8.62103 13.6666 4.8252 13.6666 4.8252 13.6666" stroke-miterlimit="10"/>
                                    <path d="M2 7.32721C2 6.97713 2.2823 6.69331 2.63053 6.69331H4.83739C5.18562 6.69331 5.46792 6.97713 5.46792 7.32721V13.6665H2.63053C2.2823 13.6665 2 13.3827 2 13.0326V7.32721Z"/>
                                </svg>
                            </div>
                            <div class="evaluatine-text">
                                ${systemMessages?.LIKE_MSG}
                            </div>
                        </div>
                        <div onclick="setDislike('${sender.uuid}')" title="${systemMessages?.DISLIKE_MSG}" class="icon-button dislike ${dislikeActive}">
                            <div>
                                <svg width="16" height="16" viewBox="0 0 16 16" xmlns="http://www.w3.org/2000/svg">
                                    <path d="M5.45573 9.29122L8.04088 13.1582C8.29309 13.5386 8.92362 13.7921 9.42805 13.602C9.99552 13.4118 10.3738 12.7778 10.2477 12.2073L9.93247 10.1787C9.86942 9.73497 10.1847 9.418 10.563 9.418H13.0851C14.0309 9.418 14.6111 8.68898 14.2831 7.76978C13.9553 6.85058 13.6653 5.20236 12.7699 3.77601C12.3601 3.12331 11.9108 2.66663 11.1432 2.66663C8.62103 2.66663 4.8252 2.66663 4.8252 2.66663" stroke-miterlimit="10"/>
                                    <path d="M2 9.00604C2 9.35612 2.2823 9.63994 2.63053 9.63994H4.83739C5.18562 9.63994 5.46792 9.35612 5.46792 9.00604V2.66671H2.63053C2.2823 2.66671 2 2.95052 2 3.30065V9.00604Z"/>
                                </svg>
                            </div>
                            <div class="evaluatine-text">
                                ${systemMessages?.DISLIKE_MSG}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            <div class="message-metadata">${sender?.name}${sender?.user_time}</div>
        </div>
    </div>
    `; 
}

function showRecievedMessage(sender, like, isUnread=false) {
    const messageItem = document.createElement('li');
    messageItem.classList.add('received');
    if (isUnread) {
        messageItem.classList.add('unread-message');
    }
    messageItem.innerHTML = createRecievedHTML(sender, like);
    hideTypingIndicator();
    if (chatType === 'bot' && !isGettingHistory) {
        regulateMessages(messagesList, messageItem);
    } else if (chatType !== 'bot' ) {
        joinResponses(messagesList, messageItem, sender, like);
    } else {
        messagesList.appendChild(messageItem); 
    }
    handleWindowSize();
    scrollTo(messagesBox.scrollTop);
    if (sender?.scroll === 'True') {
        scrollToBottom();
    }
    // max request queue
    increaseRequestQueue(5);

    negativeSummarizer(sender?.is_negative);
}

function regulateMessages(messagesList, messageItem) {
    const repetitiveRequests = getRepetitiveRequests(messagesList.children);
    if (repetitiveRequests.length > 0) {
        repetitiveRequests.forEach(request => {
            messagesList.removeChild(request);
        });
        messagesList.appendChild(messageItem);
        repetitiveRequests.forEach(request => {
            messagesList.appendChild(request);
        });
    } else {
        messagesList.appendChild(messageItem);
    }
}

function joinResponses(messagesList, messageItem, sender, like) {
    const repetitiveResponses = getRepetitiveResponses(messagesList.children)
    if (repetitiveResponses.length > 0) {
        repetitiveResponses.forEach(response => {
            messagesList.removeChild(response);
        });
        repetitiveResponses.forEach(response => {
            const messageElement = response.querySelector('.message-field > div:first-child');
            if (messageElement) {
                const messageHTML = messageElement.innerHTML;
                const liElement = document.createElement('li');
                liElement.classList.add('part-message-received');    
                liElement.innerHTML = `<div><div class="message-field message-part-text">${messageHTML}</div></div>`;   
                messagesList.appendChild(liElement); 
            }    
        });
        messageItem.innerHTML = createRecievedHTML(sender, like);
        messagesList.appendChild(messageItem);
    } else {
        messagesList.appendChild(messageItem);
    }
}

function getRepetitiveRequests(messageBox) {
    const consecutiveElements = findRepetitiveElements(messageBox, 'sent');
    if (consecutiveElements.length >= 2) {
        return consecutiveElements.slice(1);
    } else {
        return [];
    }
}

function getAllRepetitiveRequests(messageBox) {
    const consecutiveElements = findRepetitiveElements(messageBox, 'sent');
    if (consecutiveElements.length > 0) {
        return consecutiveElements;
    } else {
        return [];
    }
}

function getRepetitiveResponses(messageBox) {
    const consecutiveElements = findRepetitiveElements(messageBox, 'received');
    if (consecutiveElements.length > 0) {
        return consecutiveElements;
    } else {
        return [];
    }
}

function setLike(id) {
    reconnect();
    if (id) {
        if (chatSocket.readyState === WebSocket.OPEN) {
            chatSocket.send(JSON.stringify({
                'type' : 'grade',
                'id' : id,
                'grade' : 'like'
            }));
            const message = document.getElementById(id);
            if (message) {
                message.querySelector('.like').classList.add('active');
                message.querySelector('.dislike').classList.remove('active');
            }
        }
    }
    const lastContainerId = getLastEvaluateContainerId();
    if (id === lastContainerId) removeShowCallAgentOffer();
}

function setDislike(id) {
    reconnect();
    if (id) {
        if (chatSocket.readyState === WebSocket.OPEN) {
            chatSocket.send(JSON.stringify({
                'type' : 'grade',
                'id' : id,
                'grade' : 'dislike'
            }));
            const message = document.getElementById(id);
            if (message) {
                message.querySelector('.dislike').classList.add('active');
                message.querySelector('.like').classList.remove('active');
                const lastContainerId = getLastEvaluateContainerId();
                removeShowCallAgentOffer();
                if (id === lastContainerId && chatType === 'bot' && isIntentModel) {
                    showCallAgentOffer();              
                } 
            }
        }
    }
}

function getLastEvaluateContainerId() {
    const allContainers = document.querySelectorAll('.evaluatine-button-container');
    const lastContainer = allContainers[allContainers.length - 1];
    return lastContainer.getAttribute('id');
}

function joinOrLeftSender(sender, isJoined) {
    const messageItem = document.createElement('li');
    messageItem.id = 'sender'
        
    let userTime = sender.user_time ? sender.user_time : getCurrentDateTime() 
    messageItem.innerHTML = `    
    <div class="chat-event"> 
        <div class="avatar-icon">
            ${sender.avatar !== '' ? `<img src="${sender.avatar}" alt="${sender.name}" title="${sender.name}">` : `<div class="default-icon">${getInitials(sender.name)}</div>`}    
        </div>         
        <div class="system-event-text">${sender.name} ${isJoined ? systemMessages?.JOINED_MSG : systemMessages?.LEFT_MSG}${userTime}</div>
    </div>      
    `;
    messagesList.appendChild(messageItem); 
    scrollToBottom();
}

function showGreetings(sender) {
    const messageItem = document.createElement('li');
    messageItem.classList.add('part-message-received');
    messageItem.innerHTML = `    
    <div>
        <div class="message-field message-part-text">
            ${sender.greetings}
        </div>
    </div>
    `;
    messagesList.appendChild(messageItem);
}

function runWithDelay(func, delay, arg) {
    setTimeout(() => {
        if (arg !== undefined) {
            func(arg);
        } else {
            func();
        }
    }, delay); 
}

function showTypingIndicator(sender) {
    const messageItem = document.createElement('li');
    messageItem.classList.add('received');
    messageItem.id = 'typingIndicator';
    messageItem.innerHTML = `
        <div id="message-text" class="message-text">           
            <div class="sender-icon">
                ${sender.avatar !== '' ? `<img src="${sender.avatar}" alt="${sender?.name}" title="${sender?.name}">` : `<div class="default-icon">${getInitials(sender?.name)}</div>`}     
            </div>           
            <div class="message-block">
                <div class="typing-event message-field">
                    <div class="typing-indicator">
                      <div class="typing-dots">
                        <div class="dot"></div>
                        <div class="dot"></div>
                        <div class="dot"></div>
                      </div>
                    </div>
                </div>
                <div class="message-metadata">${sender.name} ${systemMessages?.TYPING_MSG}</div> 
            </div>
        </div>
    `;
    const typingIndicator = document.getElementById('typingIndicator');
    if (typingIndicator) {
        messagesList.removeChild(typingIndicator)
    }
    messagesList.appendChild(messageItem);
}

function showSideTypingIndicator() {
    unreadIndicator.classList.remove('hidden'); 
    unreadIndicator.innerHTML = '';
    const typingInd = document.createElement('div');
    typingInd.classList.add('side-typing-indicator');
    typingInd.innerHTML = `      
        <div class="typing-dots">
            <div class="dot"></div>
            <div class="dot"></div>
            <div class="dot"></div>
        </div>
    `;
    unreadIndicator.appendChild(typingInd);
}

function hideSideTypingIndicator() {      
    unreadIndicator.classList.add('hidden');
    unreadIndicator.innerHTML = '';
    const unreadInd = document.createElement('div');
    unreadInd.innerHTML = `      
        <div onclick="scrollTextarea();">
            <div class="unread">
            <span id="unread-counter">1</span>
            </div>
        </div> 
    `;
    unreadIndicator.appendChild(unreadInd);   
}

function hideTypingIndicator() {
    const typingIndicator = document.getElementById('typingIndicator');
    if (typingIndicator) {
        messagesList.removeChild(typingIndicator);
    }
    hideSideTypingIndicator();
}

function closeWidget(event) {    
    sendToParent({'type' : 'widget_state', 'message' : 'close'});  
    send({
        'type': 'command',
        'message': 'send_history'        
    });
}

function stopChat() {
    send({
        'type': 'command',
        'message': 'stop'        
    });
}

function getTextWidth(text, font) {
    let canvas = getTextWidth.canvas || (getTextWidth.canvas = document.createElement("canvas"));
    let context = canvas.getContext("2d");
    context.font = font;
    let metrics = context.measureText(text);
    return metrics.width;
}

textarea.addEventListener('input', (event) => {
    const value = textarea.value;
    const calc = getTextWidth(value, '16px');
    windowWidth = window.innerWidth;

    let calculatedWidth = 190;  // without attachment loader
    if (isAttachmentLoader) {
        calculatedWidth = 180; // with attachment loader
    }

    let requiredRows = Math.floor(calc / calculatedWidth) + 1;
    textarea.rows = requiredRows > 4 ? 4 : requiredRows; 

    if (!isTyping) {
        sendTypingIndicatorCommand();
        isTyping = true; 
    }

    setTimeout(() => {
        isTyping = false;
    }, 7000); 
});

function sendTypingIndicatorCommand() {
    if (chatType !== 'bot') {
        send({
            'type': 'command',
            'message': 'show_typing_indicator'        
        });
    }
}

function reconnect() {
    if (chatSocket.readyState === WebSocket.CLOSED) {  
        console.log('***Reconnect...');
        location.reload();      
    } 
}

chatContainer.addEventListener('click', (event) => {
    reconnect();
})

textarea.addEventListener('input', toggleSubmitButtonActivation);

function toggleSubmitButtonActivation() {
    const textarea = this;
    if (textarea.value.trim().length > 0) {
        submitButton.removeAttribute('disabled');
    } else {
        submitButton.setAttribute('disabled', true);
    }
}

textarea.addEventListener('keydown', handleEnterKey);

function handleEnterKey(event) {
    if (event.key === 'Enter') {
        event.preventDefault(); 
        const textarea = this;
        textarea.rows = 1;
        document.getElementById('submit').click();
        decreaseRequestQueue();
    }
}

function decreaseRequestQueue() {
    if (!isGettingHistory) {
        maxRequestQueue--;
        maxRequestQueue = maxRequestQueue < 0 ? 0 : maxRequestQueue;
        if (maxRequestQueue === 0) {
            disableTextareaForBotRequests();
            if (systemMessages?.MESSAGES_PROCESSED_MSG) {
                textarea.placeholder = systemMessages.MESSAGES_PROCESSED_MSG
            }
        }
    }
}

function increaseRequestQueue(max) {
    if (!isGettingHistory) {
        maxRequestQueue++;
        maxRequestQueue = maxRequestQueue > max ? max : maxRequestQueue;
    }
}

document.addEventListener('DOMContentLoaded', (event) => {
    
    topMenuButton.addEventListener('click', (event) => {
        if (chatSocket.readyState === WebSocket.CLOSED) {
            if (chatType === 'bot') {
                location.reload();
            }
        } 
        event.stopPropagation();    
        menu.classList.toggle('hidden');  
        overlay.classList.toggle('hidden');                              
    });

    document.addEventListener('click', (event) => {
        if (!topMenuButton.contains(event.target) && !menu.contains(event.target)) {
            menu.classList.add('hidden');
            overlay.classList.add('hidden');    
        }
    });

});

function disableAllEvaluetions() {
    const evaluetionContainers = document.querySelectorAll('.evaluatine-button-container');
    for (container of evaluetionContainers) {
        container.classList.add('disabled');
    }
}

function getCurrentDateTime() {
    const now = new Date();
    const hours = now.getHours();
    const minutes = now.getMinutes();
    const formattedMinutes = minutes < 10 ? '0' + minutes : minutes;
    const period = hours >= 12 ? 'PM' : 'AM';
    const formattedHours = hours % 12 || 12; 
    return ` • ${formattedHours}:${formattedMinutes} ${period}`;
}

function scrollToBottom(isAuto=false) {
    behavior = isAuto ? 'auto' : 'smooth';
    messagesBox.scrollTo({
        top: messagesBox.scrollHeight,
        behavior: behavior
    });
}

function scrollTo(size) {
    messagesBox.scrollTo({
        top: size,
        behavior: 'smooth'
    });
}

function checkScroll() { 
    const scrollTop = messagesBox.scrollTop; 
    const scrollHeight = messagesBox.scrollHeight - messagesBox.clientHeight;
    scrollNotInDown = scrollTop < scrollHeight - 40 || (scrollTop === 1 && scrollHeight === 1);
}

messagesBox.addEventListener('scroll', (event) => {
    getUnreadMessages();
    unreadIndicator.classList.add('hidden');
    scrollDownButton.classList.add('hidden'); 
    checkScroll();
    if (scrollNotInDown) {   
        scrollDownButton.classList.toggle('hidden'); 

        if (isUnreadResponses) {  
            unreadIndicator.classList.toggle('hidden'); 
            showUnreadCounter();
        } 
        
        if (unreadMessagesCounter > 0) {
            sendToParent({'type' : 'unread_messages_indicator', 'message' : unreadMessagesCounter});
        }           
        
        if (isLoading) {
            showSideTypingIndicator();
        }               
    } else {
        isUnreadResponses = false;
        unreadMessagesCounter = 0;
    }
    if (unreadMessagesCounter <= 0 && !isLoading) unreadIndicator.classList.add('hidden');
});

function showUnreadCounter() {
    unreadIndicator.classList.remove('hidden'); 
    const unreadCounter = document.getElementById('unread-counter');
    if (unreadCounter) {
        unreadCounter.innerHTML = unreadMessagesCounter;
    }
}

function getUnreadMessages() {
    const allMessages = messagesList.children;
    for (let i = 0; i < allMessages.length; i++) {
        const li = allMessages[i];
        if (li.classList.contains('unread-message') && isMessageVisible(li)) {
            if (unreadMessagesCounter > 0) unreadMessagesCounter--;
            li.classList.remove('unread-message');  
        }
    }
}

function isMessageVisible(message) {
    const rect = message.getBoundingClientRect();
    const containerRect = messagesBox.getBoundingClientRect();
    return rect.bottom > containerRect.top && rect.top < containerRect.bottom;
}

function scrollTextarea(event) {
    scrollToBottom();
}

function truncateString(inputString, maxLength = 2000) {
    if (inputString.length > maxLength) {
        return inputString.substring(0, maxLength);
    }
    return inputString;
}

function generateUUID() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
        const r = Math.random() * 16 | 0, v = c === 'x' ? r : (r & 0x3 | 0x8);
        return v.toString(16);
    });
}

function getInitials(name) {
    if (!name) return '';
    const parts = name.split(' ');
    const initials = [];
    if (parts[0]) {
        initials.push(parts[0].charAt(0));
    }
    if (parts[1]) {
        initials.push(parts[1].charAt(0));
    }
    return initials.join('');
}

function showAttachmentWarning(message) {
    attachmentsBox.classList.remove('hidden');
    attachmentWarningMessage.innerHTML = message;

    warningBlock.style.display = 'block';   

    setTimeout(() => {
        warningBlock.classList.remove('fade-out');
        warningBlock.classList.add('fade-in');
    }, 300)

        setTimeout(() => {
        warningBlock.classList.remove('fade-in');
        warningBlock.classList.add('fade-out');

        setTimeout(() => {
            warningBlock.style.display = 'none';
            if (attachedFiles.length === 0) {
                attachmentsBox.classList.add('hidden');
            }
        }, 500)
    }, 3000);
}

function activateSubmitButton() {
    if (attachedFiles.length > 0) {
        submitButton.removeAttribute('disabled')
    } 
}

function disactivateSubmitButton() {
    if (attachedFiles.length == 0) {
        submitButton.setAttribute('disabled', true);
    } 
}

function isValidFileType(fileType) {
    const acceptedTypes = [
        'png',
        'jpeg',
        'jpg',
        'bmp',
        'gif',
        'tiff',
        'pdf'
    ];
    return acceptedTypes.includes(fileType);
}

function getBlobData(file) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = function(event) {
            const base64Data = event.target.result;
            const base64String = base64Data.split(',')[1];
            resolve(base64String); 
        };      
        reader.onerror = function(error) {
            reject(error); 
        };
        reader.readAsDataURL(file);
    });   
}

fileUpload.addEventListener('change', (event) => {
    sendTypingIndicatorCommand();
    const files = event.target.files;
    if (files.length > 0) {
         for (let i=0;i<files.length;i++) {
             if (attachedFiles.length + 1 > 5) {
                 showAttachmentWarning(systemMessages?.ADD_UP_TO_5_ATT_MSG);     
                 fileUpload.value = null;          
                 return;
             }
             const file_type = getFileExtension(files[i].name);
             if (!isValidFileType(file_type)) {
                showAttachmentWarning(systemMessages?.UNSUPPORTED_FILE_TYPE_MSG + ' ' + files[i].name + '. ' + systemMessages?.TRY_AGAIN); 
                fileUpload.value = null;
                return;
             }
             const commonSize = calculateSizeOfAttachments();
             const fileSize = files[i].size / 1024 / 1024;
             if (commonSize + fileSize > 5) {
                 showAttachmentWarning(systemMessages?.EXCEED_5MB_LIMIT_MSG + ' ' + systemMessages?.TRY_AGAIN);
                 fileUpload.value = null;
                 return;
             }
             const exists = attachedFiles.some(attach => attach.name === files[i].name);
             if (!exists) {
                const messageId = generateUUID();
                const fileId = generateUUID();
                const fileName = files[i].name;
                
                getBlobData(files[i]).then(blobData => {       
                    const file = {
                        'id' : messageId, 
                        'file_id' : fileId,
                        'size' : fileSize, 
                        'name' : fileName,
                        'file_type' : file_type,
                        'data' : blobData
                    }
                    attachedFiles.push(file)
                    addAttachmentPill(file)
                    activateSubmitButton();      
                    
                }).catch(error => {
                    console.log('*Error reading file: ' + error);
                });                
             }         
         } 
    } 
    fileUpload.value = null;
});

function removeAttachment(id) {
    if (id) {
        const ids = attachedFiles.map(attach => attach.id)
        const index = ids.indexOf(id);
        attachedFiles.splice(index, 1);
        attachmentsList.removeChild(document.getElementById(id));
        if (attachedFiles.length <= 0) {
            attachmentsBox.classList.add('hidden');
        }
        disactivateSubmitButton();
    }
}

function sendToParent(message) {
    window.parent.postMessage(message, "*");
}

function calculateSizeOfAttachments() {
    return attachedFiles.reduce((total, file) => total + file.size, 0);
}

function getFileExtension(filename) {
    const lastDotIndex = filename.lastIndexOf('.');
    if (lastDotIndex === -1 || lastDotIndex === 0) {
        return '';
    }
    return filename.slice(lastDotIndex + 1);
}

async function downloadFile(url, fileName) {
    const link = document.createElement('a');
    link.href = url;
    link.download = fileName;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

function boldLastTwoWords(text) {
    const words = text.trim().split(/\s+/);
    if (words.length < 2) {
        return text;
    }
    const lastWord = words.pop();
    const secondLastWord = words.pop();
    const updatedText = [...words, `<strong>${secondLastWord}</strong>`, `<strong>${lastWord}</strong>`].join(' ');
    return updatedText;
}

function showCallAgentOffer() {
    const message = document.getElementById('call-agent-offer');
    if (!message) {
        const messageItem = document.createElement('li');
        messageItem.setAttribute('id', 'call-agent-offer');
        messageItem.classList.add('received');
        const textOffer = boldLastTwoWords(systemMessages?.WOULD_Y_LIKE_TO_SPEAK_TO_AGENT_MSG);
        messageItem.innerHTML = `
            <div id="message-text" class="message-text">
                <div class="sender-icon">
                    <img src="${respondent?.avatar}" alt="${respondent?.name}" title="${respondent?.name}">    
                </div>    
                <div>
                    <div class="message-block offer-block">
                        <div class="message-field"> 
                            <div class="offer-message">
                                ${textOffer}  
                            </div>
                            <div class="button-group-inline">           
                                <div class="call-agent-btn" onclick="callAgent();">
                                    ${systemMessages?.YES_MSG}
                                </div>
                                <div class="call-agent-btn" onclick="removeShowCallAgentOffer();">
                                    ${systemMessages?.NO_MSG}
                                </div>
                            </div>
                        </div>                              
                    </div>
                </div>
            </div>
            `;
        messagesList.appendChild(messageItem);
        scrollToBottom();      
        if (systemMessages?.CHOOSE_MSG) {
            textarea.placeholder = systemMessages.CHOOSE_MSG
        } 
        setTimeout(() => {
            textarea.setAttribute('disabled', 'disabled');
        }, 100)
    }
}

function removeShowCallAgentOffer() {
    const message = document.getElementById('call-agent-offer');
    if (message) {
        messagesList.removeChild(message);
    }   
    if (systemMessages?.TYPE_Y_MSG) {
        textarea.placeholder = systemMessages.TYPE_Y_MSG
    }
    textarea.removeAttribute('disabled');  
}

function callAgent() {
    reconnect();
    removeShowCallAgentOffer();
    menu.classList.toggle('hidden');  
    overlay.classList.toggle('hidden');
    send({
        'type': 'command',
        'message': 'connect_agent'            
    });
}

function clearChat() {
    send({
        'type': 'command',
        'message': 'clear_chat'            
    });
    location.reload()
}

function send(message) {
    if (chatSocket.readyState === WebSocket.OPEN) {
        chatSocket.send(JSON.stringify(message));
    }
}

function convertJsonStringToObject(jsonString) {
    try {
        const jsonObject = JSON.parse(jsonString);
        return jsonObject;
    } catch (error) {
        console.log("*Error in convert json-string to Object: " + error);
        return {}; 
    }
}

function findRepetitiveElements(liCollection, field) {
    const sentElements = [];
    for (let i = liCollection.length - 1; i >= 0; i--) {
        const li = liCollection[i];
        if (li.classList.contains(field)) {
            sentElements.push(li); 
        } else {
            break;
        }
    }

    if (sentElements.length > 0) {
        return sentElements.reverse(); 
    } else {
        return []; 
    }
}