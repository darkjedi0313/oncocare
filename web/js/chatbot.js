// Onco Chatbot Component

function initChatbot() {
    const currentPath = window.location.pathname.split('/').pop() || 'index.html';
    if (currentPath === 'login.html') return;
    // 1. Create and inject Chatbot HTML markup to the body
    const chatContainer = document.createElement('div');
    chatContainer.id = 'onco-chat-panel';
    chatContainer.className = 'fixed top-0 right-0 h-full w-[380px] bg-white border-l border-data-border-gray shadow-2xl z-50 transform translate-x-full transition-transform duration-300 ease-in-out flex flex-col justify-between font-body-md text-slate-800';
    chatContainer.innerHTML = `
        <!-- Header -->
        <div class="bg-primary text-white p-4 flex justify-between items-center flex-shrink-0">
            <div class="flex items-center gap-2">
                <span class="material-symbols-outlined text-[24px]">support_agent</span>
                <div>
                    <h4 class="font-bold text-sm">대화형 AI 온코 (Onco)</h4>
                    <p class="text-[10px] text-slate-200">검진 지표 분석 및 개입전략 상담</p>
                </div>
            </div>
            <button id="btn-close-chat" class="text-white/80 hover:text-white">
                <span class="material-symbols-outlined text-[20px]">close</span>
            </button>
        </div>

        <!-- Message Body -->
        <div id="chat-message-body" class="flex-1 p-4 overflow-y-auto space-y-3 bg-slate-50 text-xs">
            <!-- Initial greeting -->
            <div class="flex items-start gap-2">
                <div class="w-7 h-7 rounded-full bg-primary text-white flex items-center justify-center flex-shrink-0">
                    <span class="material-symbols-outlined text-[16px]">smart_toy</span>
                </div>
                <div class="bg-white border border-data-border-gray p-3 rounded-lg max-w-[80%] shadow-sm leading-relaxed">
                    안녕하세요! 온코케어의 AI 분석 비서 **온코**입니다. 
                    현재 화면에 조회된 통계 팩트를 기반으로 부진 요인 분석 및 맞춤 행동 전략에 관해 실시간 상담을 지원합니다.
                    <div class="mt-2 text-[10px] text-data-alert font-bold">⚠️ 이 값은 평가가 아니라 검토 시작점입니다.</div>
                </div>
            </div>

            <!-- Recommendation Quick Tips -->
            <div class="pt-3 space-y-1.5" id="chat-quick-chips">
                <p class="text-[10px] text-slate-400 font-bold block">💡 추천 질문</p>
                <button class="quick-chip w-full text-left p-2 bg-white hover:bg-slate-100 border border-slate-200 rounded text-slate-600 block transition-colors leading-tight" data-question="현재 세그먼트의 수검률과 격차는 얼마인가요?">
                    현재 세그먼트의 수검률과 격차는?
                </button>
                <button class="quick-chip w-full text-left p-2 bg-white hover:bg-slate-100 border border-slate-200 rounded text-slate-600 block transition-colors leading-tight" data-question="해당 대상자에게 추천되는 개입 카드와 근거를 요약해 줘.">
                    추천 개입 카드와 근거 요약
                </button>
                <button class="quick-chip w-full text-left p-2 bg-white hover:bg-slate-100 border border-slate-200 rounded text-slate-600 block transition-colors leading-tight" data-question="미수검 원인을 층화 요인 관점에서 설명해 줄래?">
                    미수검 원인을 층화 요인 관점으로 설명
                </button>
            </div>
        </div>

        <!-- Input Area -->
        <div class="p-3 border-t border-data-border-gray bg-white flex-shrink-0 flex flex-col gap-2">
            <div class="flex gap-2">
                <input type="text" id="chat-input-text" placeholder="온코에게 질문을 입력하세요..." class="flex-1 border border-data-border-gray rounded px-3 py-2 text-xs focus:outline-none focus:ring-1 focus:ring-primary focus:border-primary"/>
                <button id="btn-send-chat" class="px-3 bg-primary text-white text-xs font-bold rounded hover:bg-primary/95 transition-colors flex items-center justify-center">
                    <span class="material-symbols-outlined text-[16px]">send</span>
                </button>
            </div>
            <div class="text-[9px] text-slate-400 text-center select-none">
                보건소 발신 명의로 대답합니다. 개인정보는 송신되지 않습니다.
            </div>
        </div>
    `;
    
    document.body.appendChild(chatContainer);
    
    // 2. Event Handlers setup
    const chatPanel = document.getElementById('onco-chat-panel');
    const btnCloseChat = document.getElementById('btn-close-chat');
    const btnSendChat = document.getElementById('btn-send-chat');
    const chatInputText = document.getElementById('chat-input-text');
    const chatMessageBody = document.getElementById('chat-message-body');
    const quickChips = document.getElementById('chat-quick-chips');
    
    let chatHistory = [];
    
    function toggleChat(show) {
        if (show) {
            chatPanel.classList.remove('translate-x-full');
        } else {
            chatPanel.classList.add('translate-x-full');
        }
    }
    
    // Bind toggle action to floating button globally
    function bindFloatingButton() {
        const floatingBtn = document.getElementById('floating-btn') || document.querySelector('button[onclick*="온코"]');
        if (floatingBtn) {
            floatingBtn.removeAttribute('onclick');
            
            // 프리미엄 AI 스타일 적용 (더 큰 크기, 입체감 있는 그라데이션, 애니메이션)
            floatingBtn.className = "fixed bottom-8 right-8 w-[88px] h-[88px] bg-gradient-to-br from-[#1F4E78] via-[#008080] to-[#0EA5E9] rounded-full shadow-2xl flex flex-col items-center justify-center text-white cursor-pointer z-50 hover:from-[#256294] hover:to-[#0284c7] transition-all duration-300 hover:scale-110 border-2 border-white/20 relative overflow-hidden group";
            
            floatingBtn.innerHTML = `
                <!-- Shimmer/빛반사 효과 레이어 -->
                <div class="absolute inset-0 w-1/2 h-full bg-white/20 -skew-x-[30deg] -translate-x-full group-hover:animate-[shimmer_1.5s_infinite]"></div>
                
                <!-- AI Sparkle Icon -->
                <span class="material-symbols-outlined text-[36px] leading-none text-yellow-300 drop-shadow-md group-hover:rotate-[15deg] transition-transform duration-300" style="font-variation-settings: 'FILL' 1;">auto_awesome</span>
                <span class="font-bold mt-1 text-[13px] leading-none tracking-wider text-slate-100 group-hover:text-white drop-shadow">온코 AI</span>
                
                <!-- Glowing Aura/Sparkle Ping -->
                <span class="absolute top-1.5 right-1.5 flex h-3.5 w-3.5">
                  <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-yellow-300 opacity-75"></span>
                  <span class="relative inline-flex rounded-full h-3.5 w-3.5 bg-yellow-400"></span>
                </span>
            `;
            
            // 중복 바인딩 방지 플래그 체크
            if (!floatingBtn.dataset.bound) {
                floatingBtn.addEventListener('click', (e) => {
                    e.preventDefault();
                    e.stopPropagation(); // 이벤트 버블링 차단
                    
                    const isOpen = !chatPanel.classList.contains('translate-x-full');
                    toggleChat(!isOpen);
                });
                floatingBtn.dataset.bound = 'true';
            }
        }
    }
    
    // Run binding immediately and retry on window load
    bindFloatingButton();
    window.addEventListener('load', bindFloatingButton);
    
    btnCloseChat.addEventListener('click', () => toggleChat(false));
    
    // 3. Context gathering helper — URL 파라미터 > 전역변수 > 드롭다운 순으로 우선순위 결정
    function getContextSegment() {
        let region = '서울특별시|양천구';
        let sex = '여자';
        let age = '65~69';
        let cancer = '대장암';
        let year = 2024;
        
        // URL 파라미터에서 세그먼트 추출 (가장 높은 우선순위)
        const urlParams = new URLSearchParams(window.location.search);
        if (urlParams.get('region')) region = urlParams.get('region');
        if (urlParams.get('sex')) sex = urlParams.get('sex');
        if (urlParams.get('age')) age = urlParams.get('age');
        if (urlParams.get('cancer')) cancer = urlParams.get('cancer');
        if (urlParams.get('year')) year = parseInt(urlParams.get('year'));
        
        // 페이지 전역 변수에서 덮어쓰기 (전역변수가 있으면 URL보다 구체적)
        try {
            if (typeof currentRegion !== 'undefined' && currentRegion) region = currentRegion;
            if (typeof currentSex !== 'undefined' && currentSex) sex = currentSex;
            if (typeof currentAge !== 'undefined' && currentAge) age = currentAge;
            if (typeof currentCancer !== 'undefined' && currentCancer) cancer = currentCancer;
            if (typeof currentYear !== 'undefined' && currentYear) year = parseInt(currentYear);
        } catch(e) { /* 전역변수 미존재 시 무시 */ }
        
        // 화면 내 드롭다운에서 읽기 (가장 낮은 우선순위이지만 실시간 반영)
        const selCancer = document.getElementById('select-cancer');
        const selGender = document.getElementById('select-gender') || document.getElementById('select-sex');
        const selAge = document.getElementById('select-age');
        const selRegion = document.getElementById('select-region');
        
        if (selCancer && selCancer.value) cancer = selCancer.value;
        if (selGender && selGender.value) sex = selGender.value;
        if (selAge && selAge.value) age = selAge.value;
        if (selRegion && selRegion.value) region = selRegion.value;
        
        // 연령대 형식 정규화 ('65~69세' → '65~69')
        age = age.replace(/세$/, '').trim();
        
        return {
            segment: { region, sex, age, cancer },
            year: parseInt(year)
        };
    }
    
    async function sendUserMessage(text) {
        if (!text || text.trim() === '') return;
        
        appendMessage('user', text);
        chatInputText.value = '';
        
        if (quickChips) {
            quickChips.style.display = 'none';
        }
        
        chatHistory.push({ role: 'user', content: text });
        const loaderId = appendLoader();
        
        try {
            const ctx = getContextSegment();
            const payload = {
                segment: ctx.segment,
                year: ctx.year,
                history: chatHistory
            };
            
            const data = await postChat(payload);
            removeLoader(loaderId);
            
            let formattedReply = data.reply
                .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                .replace(/\*(.*?)\*/g, '<em>$1</em>')
                .replace(/\n/g, '<br>');
                
            appendMessage('assistant', formattedReply);
            chatHistory.push({ role: 'assistant', content: data.reply });
            
        } catch (err) {
            console.error(err);
            removeLoader(loaderId);
            appendMessage('assistant', `<span class="text-data-alert font-bold">오류가 발생했습니다: ${err.message}</span>`);
        }
    }
    
    function appendMessage(role, content) {
        const msgRow = document.createElement('div');
        msgRow.className = 'flex items-start gap-2';
        
        if (role === 'user') {
            msgRow.className += ' justify-end';
            msgRow.innerHTML = `
                <div class="bg-primary text-white p-3 rounded-lg max-w-[80%] shadow-sm leading-relaxed">
                    ${content}
                </div>
            `;
        } else {
            msgRow.innerHTML = `
                <div class="w-7 h-7 rounded-full bg-primary text-white flex items-center justify-center flex-shrink-0 animate-none">
                    <span class="material-symbols-outlined text-[16px]">smart_toy</span>
                </div>
                <div class="bg-white border border-data-border-gray p-3 rounded-lg max-w-[80%] shadow-sm leading-relaxed">
                    ${content}
                </div>
            `;
        }
        
        chatMessageBody.appendChild(msgRow);
        chatMessageBody.scrollTop = chatMessageBody.scrollHeight;
    }
    
    function appendLoader() {
        const id = 'loader-' + Date.now();
        const loaderRow = document.createElement('div');
        loaderRow.id = id;
        loaderRow.className = 'flex items-start gap-2';
        loaderRow.innerHTML = `
            <div class="w-7 h-7 rounded-full bg-primary text-white flex items-center justify-center flex-shrink-0 animate-pulse">
                <span class="material-symbols-outlined text-[16px]">smart_toy</span>
            </div>
            <div class="bg-slate-200 p-3 rounded-lg max-w-[80%] flex items-center gap-1.5">
                <div class="w-1.5 h-1.5 bg-slate-500 rounded-full animate-bounce"></div>
                <div class="w-1.5 h-1.5 bg-slate-500 rounded-full animate-bounce [animation-delay:0.2s]"></div>
                <div class="w-1.5 h-1.5 bg-slate-500 rounded-full animate-bounce [animation-delay:0.4s]"></div>
            </div>
        `;
        chatMessageBody.appendChild(loaderRow);
        chatMessageBody.scrollTop = chatMessageBody.scrollHeight;
        return id;
    }
    
    function removeLoader(id) {
        const loader = document.getElementById(id);
        if (loader) loader.remove();
    }
    
    btnSendChat.addEventListener('click', () => {
        sendUserMessage(chatInputText.value);
    });
    
    chatInputText.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            sendUserMessage(chatInputText.value);
        }
    });
    
    // Bind Quick Chips clicks dynamically
    document.addEventListener('click', (e) => {
        if (e.target && e.target.classList.contains('quick-chip')) {
            const question = e.target.getAttribute('data-question');
            sendUserMessage(question);
        }
    });
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initChatbot);
} else {
    initChatbot();
}
