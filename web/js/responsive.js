/**
 * OncoCare 모바일 접속 대응 공통 스크립트
 * - 모바일 사이드바 토글 및 오버레이 처리
 */
document.addEventListener("DOMContentLoaded", function() {
    // 1. 모바일 딤(Overlay) 레이어 생성
    let overlay = document.querySelector(".sidebar-overlay");
    if (!overlay) {
        overlay = document.createElement("div");
        overlay.className = "sidebar-overlay";
        document.body.appendChild(overlay);
    }

    const sidebar = document.querySelector(".onco-sidebar");
    if (!sidebar) return;

    // 2. 사이드바 내부에 모바일 닫기 버튼(X) 추가 (마크업 편의를 위해 JS에서 동적으로 삽입)
    let closeBtnContainer = sidebar.querySelector(".mobile-close-container");
    if (!closeBtnContainer) {
        closeBtnContainer = document.createElement("div");
        closeBtnContainer.className = "mobile-close-container lg:hidden flex justify-end mb-2";
        closeBtnContainer.innerHTML = `
            <button id="mobile-sidebar-close-btn" class="p-2 text-primary focus:outline-none">
                <span class="material-symbols-outlined text-[28px]">close</span>
            </button>
        `;
        // 사이드바 맨 위에 삽입
        sidebar.insertBefore(closeBtnContainer, sidebar.firstChild);
    }

    // 3. 글로벌 클릭 이벤트 처리 (햄버거 메뉴 열기 / 딤 영역 클릭 시 닫기)
    document.addEventListener("click", function(e) {
        // 햄버거 메뉴 열기 버튼 클릭
        const openBtn = e.target.closest("#mobile-menu-btn");
        if (openBtn) {
            sidebar.classList.add("active");
            overlay.classList.add("active");
            // 클릭 이벤트가 버블링되어 즉시 닫히지 않도록 방지
            e.stopPropagation();
            return;
        }

        // 닫기 버튼 클릭 혹은 오버레이 영역 클릭
        const closeBtn = e.target.closest("#mobile-sidebar-close-btn");
        if (closeBtn || e.target === overlay) {
            sidebar.classList.remove("active");
            overlay.classList.remove("active");
        }
    });

    // 4. 페이지 이동 시 모바일 메뉴가 열려있다면 자동으로 닫기
    window.addEventListener("resize", function() {
        if (window.innerWidth > 1024) {
            sidebar.classList.remove("active");
            overlay.classList.remove("active");
        }
    });
});
