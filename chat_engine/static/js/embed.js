if (window.chatShell && typeof window.chatShell.destroy === 'function') {
  window.chatShell.destroy();
  delete window.chatShell;
}
// Create or overwrite the global chatShell namespace/object
if (!window.chatShell) window.chatShell = {};
const cs = window.chatShell;

cs.pingGenerator = null;
cs.isConnected = false;
cs.paramsJson = typeof params !== 'undefined' ? JSON.stringify(params) : '{}';
cs.timeZone = Intl.DateTimeFormat().resolvedOptions().timeZone;
cs.language = navigator.language || navigator.userLanguage || 'unknown';
cs.styleElement = null;
cs.chatIframe = null;
cs.chatIcon = null;
cs.unreadIndicator = null;
cs.spinnerContainer = null;
cs.handleMessageEvent = null;

function init() {

cs.styleElement = document.createElement('style');
cs.styleElement.innerHTML = `
  #c-chat-widget-iframe {
    position: fixed; bottom: 40px; right: 12px; width: 0; height: 0;
    border: none; transition: width 0s, height 0s; background: transparent;
    outline: none;
    box-shadow: 10px 10px 40px rgba(0,0,0,0.08), 5px 14px 80px rgba(26,26,26,0.12);
    z-index: 1000;
  }
  #c-external-chat-icon {
    position: fixed;
    background-color: #2971DE;
    color: white;
    text-align: center;
    line-height: 50px;
    font-size: 24px;
    cursor: pointer;
    z-index: 1000;
    border: none;
    pointer-events: all;
    transition: opacity 0.3s;
  }
  .c-chat-icon-content svg.embeddedMessagingIconChat {
    width: 100%; height: 100%; vertical-align: unset;
  }
  .c-spinner-container {
    display: flex; align-items: center; justify-content: center; width: 100%; height: 100%;
  }
  .c-chat-icon-spinner {
    position: relative; right: 8px; top: 4px; width: 24px; height: 24px; transform: rotateZ(45deg);
  }
  .c-dot-element-spinner {
    position: absolute; width: 6px; height: 6px; background-color: white; border-radius: 50%;
    top: 0; left: 50%; transform-origin: 0 18px;
  }
  .c-dot1 { animation: orbit 1.2s linear infinite; opacity: 1; }
  .c-dot2 { animation: orbit 1.2s linear infinite; animation-delay: -1.1s; opacity: 0.9; }
  .c-dot3 { animation: orbit 1.2s linear infinite; animation-delay: -1.0s; opacity: 0.8; }
  .c-dot4 { animation: orbit 1.2s linear infinite; animation-delay: -0.9s; opacity: 0.7; }
  .c-dot5 { animation: orbit 1.2s linear infinite; animation-delay: -0.8s; opacity: 0.6; }
  .c-dot6 { animation: orbit 1.2s linear infinite; animation-delay: -0.7s; opacity: 0.5; }
  .c-dot7 { animation: orbit 1.2s linear infinite; animation-delay: -0.6s; opacity: 0.4; }
  .c-dot8 { animation: orbit 1.2s linear infinite; animation-delay: -0.5s; opacity: 0.3; }
  @keyframes orbit {
    0% { transform: rotate(0deg) translateX(18px) rotate(0deg); }
    100% { transform: rotate(360deg) translateX(18px) rotate(-360deg); }
  }
  @media (max-width: 480px) {
    .c-chat-widget-size { height: 100% !important; width: 100% !important; margin-top: 1px; }
    #c-chat-widget-iframe { right: 0px !important; bottom: 0px !important; }
    #c-external-chat-icon {
      bottom: 15%; right: 0px; width: 48px; height: 48px;
      border-radius: 50% 0 0 50%;
      box-shadow: 0px 2px 32px rgba(0,0,0,0.16), 0px 1px 6px rgba(0,0,0,0.06);
    }
    .c-chat-icon-content { margin-bottom: 300%; }
    .c-chat-icon-content svg.embeddedMessagingIconChat {
      max-height: 24px; max-width: 24px; margin-top: 12px;
    }
    .c-chat-unread-indicator { right: 6px; top: 6px; height: 16px; width: 14px; font-size: 10px; line-height: 12px; }
  }
  @media (min-width: 481px) {
    .c-chat-widget-size { height: 73.3% !important; width: 432px !important; }
    #c-chat-widget-iframe { border-radius: 18px; }
    #c-external-chat-icon {
      bottom: 46px; right: 16px; width: 60px; height: 60px;
      border-radius: 50%;
      box-shadow: 0px 2px 32px rgba(0,0,0,0.16), 0px 1px 6px rgba(0,0,0,0.06);
    }
    .c-chat-icon-content { margin-bottom: 40px; }
    .c-chat-icon-content svg.embeddedMessagingIconChat {
      max-height: 32px; max-width: 32px; margin-top: 14px;
    }
    .c-chat-unread-indicator { right: -3px; top: -1px; height: 20px; width: 19px; font-size: 12px; line-height: 16px; }
  }
  .c-chat-unread-indicator {
    display: flex; position: absolute; justify-content: center; align-items: center;
    background: #C83E38; color: #FFFFFF; border-radius: 2px;
    font-family: 'Roboto', 'Arial'; font-weight: 500;
  }
  .c-chat-block-hidden { display: none !important; }
`;
document.head.appendChild(cs.styleElement);

const userId = getUserId();
cs.chatIframe = createChatIframe(userId);
document.body.appendChild(cs.chatIframe);
// --- Create unread messages indicator and spinner ---
cs.unreadIndicator = createUnreadIndicator();
cs.spinnerContainer = createSpinner();
// --- Create chat icon ---
cs.chatIcon = createChatIcon(() => handleChatIconClick(cs.chatIcon));
cs.chatIcon.appendChild(cs.spinnerContainer);
cs.chatIcon.appendChild(cs.unreadIndicator);
// Insert chat icon into body, if needed (your code had it commented out)
// document.body.appendChild(cs.chatIcon);
cs.handleMessageEvent = (event) => handleMessageEvent(event, cs.chatIcon);
window.addEventListener('message', cs.handleMessageEvent);

if (localStorage.getItem('widget_state') === 'open') {
  cs.chatIcon.click();
  cs.chatIframe.classList.add('c-chat-widget-size');
}
// --- Show unread count if any from localStorage ---
const unreadCount = localStorage.getItem('c.chat.uread.messages.count') || 0;
if (unreadCount > 0) {
  unreadIndicatorHandler(unreadCount);
}
}
// Destroy Widget
cs.destroy = function() {
if (cs.pingGenerator) {
  clearInterval(cs.pingGenerator);
  cs.pingGenerator = null;
}
if (cs.chatIframe && cs.chatIframe.parentNode) {
  cs.chatIframe.parentNode.removeChild(cs.chatIframe);
  cs.chatIframe = null;
}
if (cs.styleElement && cs.styleElement.parentNode) {
  cs.styleElement.parentNode.removeChild(cs.styleElement);
  cs.styleElement = null;
}
if (cs.chatIcon && cs.chatIcon.parentNode) {
  cs.chatIcon.parentNode.removeChild(cs.chatIcon);
  cs.chatIcon = null;
}
if (cs.unreadIndicator && cs.unreadIndicator.parentNode) {
  cs.unreadIndicator.parentNode.removeChild(cs.unreadIndicator);
  cs.unreadIndicator = null;
}
if (cs.spinnerContainer && cs.spinnerContainer.parentNode) {
  cs.spinnerContainer.parentNode.removeChild(cs.spinnerContainer);
  cs.spinnerContainer = null;
}
if (cs.handleMessageEvent) {
  window.removeEventListener('message', cs.handleMessageEvent);
  cs.handleMessageEvent = null;
}
cs.isConnected = false;
};

function createChatIcon(onClick) {
const chatIcon = document.createElement('div');
chatIcon.id = 'c-external-chat-icon';
chatIcon.innerHTML = `
  <div class="c-chat-icon-content">
    <svg id="embeddedMessagingIconChat" class="embeddedMessagingIconChat" width="32" height="32" viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M14.6667 10.6667V21.3333H20.0707L25.3333 25.3333V21.3333H28V10.6667H14.6667Z" fill="white"/>
      <path d="M4 6.66667V17.3333H6.66667V21.3333L11.9293 17.3333H17.3333V6.66667H4Z" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
      <path d="M14.6667 10.6667V21.3333H20.0707L25.3333 25.3333V21.3333H28V10.6667H14.6667Z" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
      <path d="M18.25 15C17.8358 15 17.5 15.3358 17.5 15.75C17.5 16.1642 17.8358 16.5 18.25 16.5C18.6642 16.5 19 16.1642 19 15.75C19 15.3358 18.6642 15 18.25 15Z" fill="#2971DE"/>
      <path d="M22 15.75C22 16.1642 21.6642 16.5 21.25 16.5C20.8358 16.5 20.5 16.1642 20.5 15.75C20.5 15.3358 20.8358 15 21.25 15C21.6642 15 22 15.3358 22 15.75Z" fill="#2971DE"/>
      <path d="M24.25 16.5C24.6642 16.5 25 16.1642 25 15.75C25 15.3358 24.6642 15 24.25 15C23.8358 15 23.5 15.3358 23.5 15.75C23.5 16.1642 23.8358 16.5 24.25 16.5Z" fill="#2971DE"/>
    </svg>
  </div>
`;
chatIcon.addEventListener('click', onClick);
return chatIcon;
}

// Creates unread message indicator div
function createUnreadIndicator() {
const indicator = document.createElement('div');
indicator.className = 'c-chat-unread-indicator c-chat-block-hidden';
return indicator;
}

// Creates spinner animation container
function createSpinner() {
const spinnerContainer = document.createElement('div');
spinnerContainer.className = 'c-spinner-container';
const spinner = document.createElement('div');
spinner.className = 'c-chat-icon-spinner';

for (let i = 1; i <= 8; i++) {
  const dot = document.createElement('div');
  dot.className = `c-dot-element-spinner c-dot${i}`;
  spinner.appendChild(dot);
}
spinnerContainer.appendChild(spinner);
return spinnerContainer;
}

// Creates chat iframe element
function createChatIframe(userId) {
let iframe = document.createElement('iframe');
iframe = setIframeParams(iframe, userId)
iframe.id = 'c-chat-widget-iframe';
return iframe;
}

// Handle click on chat icon
function handleChatIconClick(chatIcon) {
sendUserData();
const chatIconContent = chatIcon.querySelector('.c-chat-icon-content');
chatIconContent.style.display = 'none';

setTimeout(() => {
  showWidget();
}, 100);

localStorage.setItem('widget_state', 'open');
resetUnreadCounter();
}

// Show chat widget by adjusting iframe and hiding icon
function showWidget() {
if (cs.chatIcon) cs.chatIcon.style.display = 'none';
if (cs.chatIframe) cs.chatIframe.classList.add('c-chat-widget-size');
}

// Collapse chat widget, show icon
function collapse_widget(chatIcon) {
if (cs.chatIframe) cs.chatIframe.classList.remove('c-chat-widget-size');
if (chatIcon) {
  chatIcon.style.display = 'block';
  const content = chatIcon.querySelector('.c-chat-icon-content');
  if (content) content.style.display = 'block';
}
}

// Collapse widget & store state closed in localStorage
function collapse_widget_with_state(chatIcon) {
collapse_widget(chatIcon);
localStorage.setItem('widget_state', 'closed');
}

// Handle postMessage events from iframe
function handleMessageEvent(event, chatIcon) {
if (!event.origin || event.origin !== serverUrl) return; // security check
const type = event.data?.type;
if (!type) return;

switch(type) {
  case 'widget_state': {
    const message = event.data?.message;
    if (message === 'close') {
      collapse_widget_with_state(chatIcon);
    }
    break;
  }
  case 'user_data_request': {
    sendUserData();
    break;
  }
  case 'unread_messages_indicator': {
    const unreadMessages = event.data?.message || 0;
    setUnreadIndicator(unreadMessages, 500)
    break;
  }
  case 'restart': {       
    // it works only for login or logout
    const userId = event.data?.user_id;
    const previousConnectedUserId = localStorage.getItem('userId');  
    const unauthorisedUserId = localStorage.getItem('unauthUserId');
    if ((userId !== '' && userId !== previousConnectedUserId) || (userId === '' && previousConnectedUserId !== unauthorisedUserId)) {
      localStorage.setItem('user_token', event.data?.user_token);
      sendMessageToChild({'type' : 'restart_backend'}, 0);
    }        
    break;
  }
  case 'restart_frontend': {
    restartChatConnection(event.data?.user_id);
    break;
  }
  case 'connect': {
    cs.isConnected = true;
    if (cs.chatIcon) {
      cs.chatIcon.remove();
    }
    document.body.appendChild(chatIcon);
    if (localStorage.getItem('widget_state') === 'open') {
      chatIcon.click();
      if (cs.chatIframe) cs.chatIframe.classList.add('c-chat-widget-size');
    }
    if (cs.pingGenerator) clearInterval(cs.pingGenerator);
    break;
  }
  case 'disconnect': {
    cs.isConnected = false;
    if (cs.chatIcon && cs.chatIcon.parentNode) {
      cs.chatIcon.parentNode.removeChild(cs.chatIcon);
    }
    if (localStorage.getItem('widget_state') === 'open') {
      collapse_widget(chatIcon);
    }
    if (!cs.pingGenerator) {
      cs.pingGenerator = setInterval(() => {
        reloadIframe();
      }, 3000);
    }
    break;
  }
  case 'reload_page_hard': {
    reloadPage();
    break;
  }
  default:
    // Other messages ignored
}
}

function setUnreadIndicator(unreadMessages, time) {
  setTimeout(() => {
      localStorage.setItem('c.chat.uread.messages.count', unreadMessages);
      unreadIndicatorHandler(unreadMessages);
  }, time);
}

// Reset unread messages counter and update indicator
function resetUnreadCounter() {
localStorage.setItem('c.chat.uread.messages.count', 0);
unreadIndicatorHandler(0);
}

// Show/hide unread indicator with count
function unreadIndicatorHandler(counter) {
if (!cs.unreadIndicator) return;
if (counter > 0) {
  cs.unreadIndicator.classList.remove('c-chat-block-hidden');
} else {
  cs.unreadIndicator.classList.add('c-chat-block-hidden');
}
cs.unreadIndicator.innerHTML = counter;
}

// Send user data message to iframe child
function sendUserData() {
sendMessageToChild({
  'type' : 'user_data',
  'time_zone' : cs.timeZone,
  'widget_url' : getBaseUrl(),
  'user_id' : localStorage.getItem('userId'),
}, 0);
}

// Helper to get current base URL
function getBaseUrl() {
try {
  const parsedUrl = new URL(window.location.href);
  return `${parsedUrl.protocol}//${parsedUrl.hostname}${parsedUrl.pathname}`;
} catch {
  return window.location.origin;
}
}

function isAthorized(str) {
    return str.includes('auth');
}

// Generate UUID for user
function generateUUID() {
return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
  const r = Math.random() * 16 | 0, v = c === 'x' ? r : (r & 0x3 | 0x8);
  return v.toString(16);
});
}

// Retrieve or create user id
function getUserId() {
  let userId = localStorage.getItem('userId');
  let unauthorisedUserId = localStorage.getItem('unauthUserId');
  if (!userId || !unauthorisedUserId) {
    userId = generateUUID();
    localStorage.setItem('userId', userId);
    localStorage.setItem('unauthUserId', userId);
  }
  checkAndShowUnreadIndicator();
  return userId;
}

function checkAndShowUnreadIndicator() {
  if (!localStorage.getItem('is_chat_first_interaction')) {
    // Show 1 unread message for the first interaction
    setUnreadIndicator(1, 2000);
    localStorage.setItem('is_chat_first_interaction', 'true'); 
  }
}

// Get approximate screen size descriptor
function getScreenSize() {
const size = window.innerWidth;
if (size <= 480) {
  return 'mobile';
}
return 'desktop';
}

// Post message to iframe child window with delay
function sendMessageToChild(message, delay) {
setTimeout(() => {
  const iframe = document.getElementById('c-chat-widget-iframe');
  if (iframe && iframe.contentWindow) {
    iframe.contentWindow.postMessage(message, '*');
  }
}, delay);
}

// Detect browser type
function getBrowserType() {
const userAgent = navigator.userAgent;
if (userAgent.indexOf("Chrome") > -1) {
  if (userAgent.indexOf("Edg") > -1) {
    return "Edge"; // Microsoft Edge
  } else if (userAgent.indexOf("OPR") > -1) {
    return "Opera"; // Opera
  }
  return "Chrome"; // Google Chrome
} else if (userAgent.indexOf("Firefox") > -1) {
  return "Firefox"; // Mozilla Firefox
} else if (userAgent.indexOf("Safari") > -1) {
  if (userAgent.indexOf("Chrome") > -1) {
    return "Chrome"; // sometimes Chrome appears in Safari UA
  }
  return "Safari"; // Apple Safari
} else if (userAgent.indexOf("MSIE") > -1 || userAgent.indexOf("Trident") > -1) {
  return "Internet Explorer";
} else if (userAgent.indexOf("OPR") > -1) {
  return "Opera";
} else if (userAgent.indexOf("Brave") > -1) {
  return "Brave";
} else if (userAgent.indexOf("Vivaldi") > -1) {
  return "Vivaldi";
}
return "Unknown Browser";
}

function getOsType() {
  const userAgent = navigator.userAgent;
  if (!userAgent || typeof userAgent !== 'string' || userAgent.trim().length === 0) {
        return 'unknown';
    }
    if (/android/i.test(userAgent)) {
        return 'android';
    }
    if (/iPad|iPhone|iPod/i.test(userAgent)) {
        return 'ios';
    }
    if (/Windows NT/i.test(userAgent)) {
        return 'windows';
    }
    if (/Mac OS X|Macintosh/i.test(userAgent)) {
        return 'macos';
    }
    if (/Linux/i.test(userAgent)) {
        return 'linux';
    }
    return 'unknown';
}

function getDeviceType() {
    const userAgent = navigator.userAgent;
    if (!userAgent || typeof userAgent !== 'string' || userAgent.trim().length === 0) {
        return 'unknown';
    }
    if (/Mobi|Android.*Mobile|iPhone|Windows Phone/i.test(userAgent)) {
        return 'mobile';
    }
    if (/Tablet|iPad|Android(?!.*Mobile)/i.test(userAgent)) {
        return 'tablet';
    }
    if (/Windows NT|Macintosh|Linux|X11/i.test(userAgent)) {
        return 'desktop';
    }
    return 'unknown';
}

function setIframeParams(iframe, userId) {
  iframe.src = `${serverUrl}/chat/${userId}/?params=${encodeURIComponent(cs.paramsJson)}`;
  const className = isAthorized(userId) ? 'authorized' : 'unauthorized';
  iframe.className = className;
  return iframe;
}

function restartChatConnection(userId) {
  if (!userId) {
    userId = localStorage.getItem('unauthUserId');
    localStorage.removeItem('userId');
    if (!userId) {
      userId = generateUUID();
    }
  }
  localStorage.setItem('userId', userId);
  if (cs.chatIframe) {
    cs.chatIframe = setIframeParams(cs.chatIframe, userId);
  }
  resetUnreadCounter();
}

function reloadIframe() {
console.log('*** Iframe reloading...');
if (cs.chatIframe && cs.chatIframe.parentNode) {
  cs.chatIframe.parentNode.removeChild(cs.chatIframe);
}
const existed_frame = document.getElementById('c-chat-widget-iframe');
if (!existed_frame) {
  const userId = getUserId();
  cs.chatIframe = createChatIframe(userId);
  document.body.appendChild(cs.chatIframe);
}
}

function reloadPage() {
location.reload();
}

document.addEventListener('visibilitychange', function() {
if (document.visibilityState === 'visible' && !cs.isConnected) {
  console.log('*** ACTIVE');
  reloadIframe();
}
});

init();

// Debug logs (optional)
console.log('USER_ID: ' + localStorage.getItem('userId'));
console.log('URL: ' + window.location.href);