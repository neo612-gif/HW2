document.addEventListener('DOMContentLoaded', () => {
    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('file-input');
    const preview = document.getElementById('image-preview');
    const recommendBtn = document.getElementById('recommend-btn');
    const loader = document.getElementById('loader');
    const resultView = document.getElementById('result-view');
    const emptyView = document.getElementById('empty-view');
    const analysisBadges = document.getElementById('analysis-badges');
    const recommendationList = document.getElementById('recommendation-list');

    let selectedFile = null;

    // Trigger file input on click
    dropZone.addEventListener('click', () => fileInput.click());

    // Drag and Drop
    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('dragover');
    });

    dropZone.addEventListener('dragleave', () => dropZone.classList.remove('dragover'));

    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('dragover');
        if (e.dataTransfer.files.length) {
            handleFile(e.dataTransfer.files[0]);
        }
    });

    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length) {
            handleFile(e.target.files[0]);
        }
    });

    function handleFile(file) {
        if (!file.type.startsWith('image/')) {
            alert('이미지 파일만 선택 가능합니다.');
            return;
        }
        selectedFile = file;
        const reader = new FileReader();
        reader.onload = (e) => {
            preview.src = e.target.result;
            preview.style.display = 'block';
            dropZone.querySelector('.upload-icon').style.display = 'none';
            dropZone.querySelector('.upload-text').style.display = 'none';
            dropZone.querySelector('.upload-hint').style.display = 'none';
            recommendBtn.disabled = false;
        };
        reader.readAsDataURL(file);
    }

    // API Call
    recommendBtn.addEventListener('click', async () => {
        if (!selectedFile) return;

        const season = document.getElementById('season-select').value;
        const style = document.getElementById('style-select').value;

        // UI States
        recommendBtn.disabled = true;
        emptyView.style.display = 'none';
        resultView.style.display = 'none';
        loader.style.display = 'block';

        const formData = new FormData();
        formData.append('image', selectedFile);
        formData.append('season', season);
        formData.append('style', style);

        try {
            const response = await fetch('/api/v1/recommend/', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) throw new Error('추천을 가져오는데 실패했습니다.');

            const data = await response.json();
            renderResults(data);
        } catch (error) {
            alert(error.message);
            emptyView.style.display = 'block';
        } finally {
            loader.style.display = 'none';
            recommendBtn.disabled = false;
        }
    });

    function renderResults(data) {
        // Clear previous results
        analysisBadges.innerHTML = '';
        recommendationList.innerHTML = '';

        // Render Analysis Badges
        const analysis = data.analysis;
        const badges = [
            { label: '체형', value: analysis.detected_body_type },
            { label: '피부톤', value: analysis.detected_skin_tone },
            { label: '주요 색상', value: analysis.dominant_colors.join(', ') }
        ];

        badges.forEach(b => {
            const badge = document.createElement('div');
            badge.className = 'badge';
            badge.innerHTML = `<span style="color:var(--text-muted)">${b.label}:</span> ${b.value}`;
            analysisBadges.appendChild(badge);
        });

        // Render Recommendations (List of OutfitCombination)
        data.recommendations.forEach(combo => {
            const card = document.createElement('div');
            card.className = 'outfit-card';
            card.style.borderLeft = '4px solid var(--accent-primary)';
            
            card.innerHTML = `
                <div class="item-category">${combo.style_theme} - ${combo.occasion}</div>
                <div style="margin-bottom: 1rem;">
                    <p><strong>상의:</strong> ${combo.top.color} ${combo.top.name}</p>
                    <p><strong>하의:</strong> ${combo.bottom.color} ${combo.bottom.name}</p>
                </div>
                <div class="item-desc" style="font-style: italic;">"${combo.reason}"</div>
                <div style="margin-top:0.8rem; font-size:0.8rem; color:var(--accent-secondary)">조합 점수: ${(combo.overall_score * 100).toFixed(0)}점</div>
            `;
            recommendationList.appendChild(card);
        });

        resultView.style.display = 'flex';
    }
});
