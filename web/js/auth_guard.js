// OncoCare Authentication & Authorization Guard
// 모든 메뉴는 그대로 노출하되, 보건소 계정만 전국 모니터링 진입 시 차단
// 사이드바 최하단에 로그인 상태 + 로그아웃 버튼 배치
// 사이드바 active 메뉴 동적 강조 처리 및 페르소나 배지 자동 표시

(function() {
    // 1. 로그인 세션 검증 — 미로그인 시 login.html로 리다이렉트
    const sessionStr = localStorage.getItem('onco_session');
    const currentPath = window.location.pathname.split('/').pop() || 'index.html';

    // login.html 자체에서는 가드 동작하지 않음
    if (currentPath === 'login.html') return;

    if (!sessionStr) {
        window.location.href = 'login.html';
        return;
    }

    const session = JSON.parse(sessionStr);
    const role = session.role;

    // 2. 모든 회원 전국 모니터링 접근 허용 (제한 없음)

    // 3. DOM 로드 후 UI 커스텀
    document.addEventListener('DOMContentLoaded', () => {
        // --- C-3. 사이드바 로고 영역 밑에 페르소나 배지 동적 생성 ---
        const logoDiv = document.querySelector('nav div.mb-8');
        if (logoDiv) {
            const badge = document.createElement('div');
            badge.className = 'mt-3 px-2.5 py-1 bg-primary/10 text-primary text-[12px] font-bold rounded-md inline-flex items-center gap-1.5 border border-primary/20';
            
            let icon = 'shield_person';
            if (role === 'healthcenter') icon = 'local_hospital';
            else if (role === 'mohw') icon = 'gavel';
            else if (role === 'ncc') icon = 'biotech';
            else if (role === 'rcc') icon = 'domain';

            badge.innerHTML = `
                <span class="material-symbols-outlined text-[16px]">${icon}</span>
                ${session.label}
            `;
            logoDiv.appendChild(badge);
        }

        // --- C-2. 사이드바 메뉴 active 상태 동적화 ---
        const navLinks = document.querySelectorAll('nav ul li a');
        navLinks.forEach(link => {
            const href = link.getAttribute('href');
            
            // 기본 비활성 스타일 적용
            link.className = 'flex items-center gap-3 px-3 py-2 text-on-surface-variant font-body-md text-body-md hover:bg-data-border-gray rounded-lg transition-colors duration-200';
            const iconSpan = link.querySelector('.material-symbols-outlined');
            if (iconSpan) {
                iconSpan.removeAttribute('style');
            }

            // 현재 주소와 일치하는 메뉴 활성화
            if (href === currentPath) {
                link.className = 'flex items-center gap-3 px-3 py-2 bg-primary text-white font-body-md-bold text-body-md-bold rounded-lg transition-colors duration-200';
                if (iconSpan) {
                    iconSpan.style.variationSettings = "'FILL' 1";
                }
            }
        });

        // --- 사이드바 최하단에 로그인 상태 + 로그아웃 버튼 삽입 ---
        const sidebar = document.querySelector('nav');
        if (sidebar) {
            // disclaimer div 찾기
            const disclaimerDiv = sidebar.querySelector('.mt-auto');

            // 로그인 정보 + 로그아웃 버튼 컨테이너
            const authContainer = document.createElement('div');
            authContainer.className = 'mt-auto pt-4 border-t border-data-border-gray';
            authContainer.innerHTML = `
                <button id="btn-logout" class="flex items-center gap-2 w-full px-3 py-2 text-on-surface-variant font-body-md text-body-md hover:bg-data-border-gray rounded-lg transition-colors duration-200 cursor-pointer">
                    <span class="material-symbols-outlined" style="font-size:20px;">logout</span>
                    로그아웃
                </button>
            `;

            if (disclaimerDiv) {
                disclaimerDiv.classList.remove('mt-auto');
                disclaimerDiv.classList.add('mt-3');
                sidebar.insertBefore(authContainer, disclaimerDiv);
            } else {
                sidebar.appendChild(authContainer);
            }

            document.getElementById('btn-logout').addEventListener('click', () => {
                if (confirm('로그아웃 하시겠습니까?')) {
                    localStorage.removeItem('onco_session');
                    window.location.href = 'login.html';
                }
            });
        }

        // --- 스코프 락 — 보건소: 양천구 고정, 지역암센터: 시도 고정 ---
        if (role === 'healthcenter') {
            const sidoSelect = document.getElementById('select-sido');
            const sggSelect = document.getElementById('select-sgg');
            
            if (sidoSelect && sggSelect) {
                const [sido, sgg] = session.assigned_region.split('|');
                sidoSelect.value = sido;
                sidoSelect.disabled = true;
                
                setTimeout(() => {
                    sggSelect.value = sgg;
                    sggSelect.disabled = true;
                }, 100);
            }
            
            const urlParams = new URLSearchParams(window.location.search);
            const queryRegion = urlParams.get('region');
            if (queryRegion && queryRegion !== session.assigned_region) {
                urlParams.set('region', session.assigned_region);
                window.location.search = urlParams.toString();
            }
        }
        else if (role === 'rcc') {
            const sidoSelect = document.getElementById('select-sido');
            if (sidoSelect) {
                sidoSelect.value = session.assigned_region;
                sidoSelect.disabled = true;
            }
            
            const urlParams = new URLSearchParams(window.location.search);
            const queryRegion = urlParams.get('region');
            if (queryRegion && !queryRegion.startsWith(session.assigned_region)) {
                urlParams.set('region', '서울특별시|종로구');
                window.location.search = urlParams.toString();
            }
        }
    });
})();
