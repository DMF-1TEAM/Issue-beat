document.addEventListener("DOMContentLoaded", () => {
    const image1 = document.getElementById("splash-image-1");
    const image2 = document.getElementById("splash-image-2");
    const text = document.getElementById("splash-text");
    const logo = document.getElementById("splash-logo");

    // 첫 번째 이미지 -> 두 번째 이미지로 전환
    setTimeout(() => {
        image1.style.opacity = "0"; // 첫 번째 사진 숨기기
        image2.style.opacity = "1"; // 두 번째 사진 나타내기

        // 글자와 로고 나타내기
        setTimeout(() => {
            text.style.opacity = "1"; // 글자 표시
            text.style.transform = "translateY(0)"; // 글자 애니메이션
            logo.style.opacity = "1"; // 로고 표시

            // 홈으로 이동
            setTimeout(() => {
                window.location.href = "home/"; // 홈 페이지로 이동
            }, 2000); // 대기 시간 (2초)
        }, 1000); // 두 번째 이미지 표시 후 1초 대기
    }, 500); // 첫 번째 이미지 표시 시간
});