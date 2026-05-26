/** KidsColorAI Frontend Application */

document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('generate-form');
    const statusSection = document.getElementById('status-section');
    const resultsSection = document.getElementById('results-section');
    const progressFill = document.getElementById('progress-fill');
    const statusMessage = document.getElementById('status-message');
    const downloadBtn = document.getElementById('download-btn');
    const pagesGrid = document.getElementById('pages-grid');
    const characterSection = document.getElementById('character-section');
    const characterInfo = document.getElementById('character-info');
    const storyPlanSection = document.getElementById('story-plan-section');
    const storyPlanGrid = document.getElementById('story-plan-grid');

    let currentJobId = null;
    let pollInterval = null;

    if (downloadBtn) {
        downloadBtn.addEventListener('click', () => {
            window.location.href = `/api/pdf/${currentJobId}`;
        });
    }

    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        const theme = document.getElementById('theme').value;
        const pageCount = document.getElementById('page-count').value;
        const imageSize = document.getElementById('image-size').value;

        const response = await fetch('/api/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ theme, page_count: parseInt(pageCount), image_size: parseInt(imageSize) })
        });

        const job = await response.json();
        currentJobId = job.id;
        statusSection.classList.remove('hidden');
        resultsSection.classList.add('hidden');
        downloadBtn.classList.add('hidden');
        characterSection.classList.add('hidden');
        storyPlanSection.classList.add('hidden');

        pollInterval = setInterval(checkStatus, 2000);
    });

    async function checkStatus() {
        if (!currentJobId) return;

        const response = await fetch(`/api/job/${currentJobId}`);
        const status = await response.json();

        progressFill.style.width = `${status.progress}%`;
        statusMessage.textContent = status.message;

        if (status.character) {
            characterSection.classList.remove('hidden');
            characterInfo.innerHTML = `
                <h3>${status.character.name}</h3>
                <p><strong>Description:</strong> ${status.character.description}</p>
                <p><strong>Appearance:</strong> ${status.character.appearance}</p>
                <p><strong>Personality:</strong> ${status.character.personality}</p>
            `;
        }

        if (status.story_pages && status.story_pages.length > 0) {
            storyPlanSection.classList.remove('hidden');
            storyPlanGrid.innerHTML = status.story_pages.map(page => `
                <div class="story-page-item">
                    <h4>Page ${page.page_number}</h4>
                    <p class="story-text">${page.story_text}</p>
                    <p class="image-prompt"><strong>Image Prompt:</strong> ${page.image_prompt}</p>
                </div>
            `).join('');
        }

        if (status.status === 'COMPLETED') {
            clearInterval(pollInterval);
            loadPages();
            downloadBtn.classList.remove('hidden');
        } else if (status.status === 'FAILED') {
            clearInterval(pollInterval);
            statusMessage.textContent = 'Generation failed. Please try again.';
        }
    }

    async function loadPages() {
        const response = await fetch(`/api/pages/${currentJobId}`);
        const pages = await response.json();

        pagesGrid.innerHTML = pages.map(page => `
            <div class="page-item">
                <img src="${page.image_path}" alt="Page ${page.id}">
                <p>${page.story_text}</p>
                <p class="prompt"><small>Prompt: ${page.image_prompt || page.prompt_used}</small></p>
            </div>
        `).join('');

        resultsSection.classList.remove('hidden');
    }
});