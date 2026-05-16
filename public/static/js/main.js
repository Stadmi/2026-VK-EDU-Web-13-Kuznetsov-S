document.addEventListener('DOMContentLoaded', () => {

    // ── CSRF ─────────────────────────────────────────────────────────────────
    function getCsrfToken() {
        const cookie = document.cookie.split(';').find(c => c.trim().startsWith('csrftoken='));
        return cookie ? decodeURIComponent(cookie.split('=')[1]) : '';
    }

    function postJson(url, body) {
        return fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCsrfToken() },
            body: JSON.stringify(body),
        }).then(r => r.json());
    }

    // ── Vote widget ───────────────────────────────────────────────────────────
    function initVoteWidget(widget) {
        const type = widget.dataset.type;
        const id   = parseInt(widget.dataset.id, 10);
        const upBtn    = widget.querySelector('.vote-btn.up');
        const downBtn  = widget.querySelector('.vote-btn.down');
        const countSpan = widget.querySelector('.vote-count');
        if (!upBtn || !downBtn) return;

        function handleVote(value) {
            const url = type === 'question' ? '/vote/question/' : '/vote/answer/';
            postJson(url, { id, value })
                .then(data => {
                    if (data.error) {
                        if (data.redirect) { window.location.href = data.redirect; return; }
                        alert('Ошибка: ' + (typeof data.error === 'string' ? data.error : JSON.stringify(data.error)));
                        return;
                    }
                    countSpan.textContent = data.rating;
                    upBtn.classList.toggle('active', data.user_vote === 1);
                    downBtn.classList.toggle('active', data.user_vote === -1);
                })
                .catch(() => alert('Ошибка соединения.'));
        }

        upBtn.addEventListener('click', () => handleVote(1));
        downBtn.addEventListener('click', () => handleVote(-1));
    }

    document.querySelectorAll('.vote-widget').forEach(initVoteWidget);
    window.__initVoteWidget = initVoteWidget;

    // ── Mark correct ─────────────────────────────────────────────────────────
    document.querySelectorAll('.mark-correct-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            postJson('/mark-correct/', { answer_id: parseInt(btn.dataset.answerId, 10) })
                .then(data => {
                    if (data.error) {
                        if (data.redirect) { window.location.href = data.redirect; return; }
                        alert('Ошибка: ' + data.error);
                        return;
                    }
                    document.querySelectorAll('.mark-correct-btn').forEach(b => {
                        const isThis    = parseInt(b.dataset.answerId, 10) === data.answer_id;
                        const isCorrect = isThis && data.is_correct;
                        b.textContent = isCorrect ? '✓ Правильный' : 'Отметить верным';
                        b.classList.toggle('btn-success', isCorrect);
                        b.classList.toggle('btn-outline-success', !isCorrect);
                        const card = b.closest('article');
                        if (card) {
                            card.classList.toggle('correct', isCorrect);
                            card.classList.toggle('border-success', isCorrect);
                            const badge = card.querySelector('.correct-badge');
                            if (badge) badge.classList.toggle('d-none', !isCorrect);
                        }
                    });
                })
                .catch(() => alert('Ошибка соединения.'));
        });
    });

    // ── Search with debounce ──────────────────────────────────────────────────
    const searchInput    = document.getElementById('search-input');
    const searchDropdown = document.getElementById('search-dropdown');

    if (searchInput && searchDropdown) {
        let debounceTimer;

        searchInput.addEventListener('input', () => {
            clearTimeout(debounceTimer);
            const q = searchInput.value.trim();
            if (q.length < 2) {
                searchDropdown.classList.add('d-none');
                searchDropdown.innerHTML = '';
                return;
            }
            debounceTimer = setTimeout(() => {
                fetch(`/search/?q=${encodeURIComponent(q)}`)
                    .then(r => r.json())
                    .then(data => {
                        searchDropdown.innerHTML = '';
                        if (!data.results || data.results.length === 0) {
                            searchDropdown.classList.add('d-none');
                            return;
                        }
                        data.results.forEach(item => {
                            const li = document.createElement('li');
                            li.innerHTML = `<a href="${item.url}" class="d-block px-3 py-2 text-decoration-none text-dark search-item">${escHtml(item.title)}</a>`;
                            searchDropdown.appendChild(li);
                        });
                        searchDropdown.classList.remove('d-none');
                    })
                    .catch(() => {});
            }, 300);
        });

        document.addEventListener('click', e => {
            if (!document.getElementById('search-wrapper')?.contains(e.target)) {
                searchDropdown.classList.add('d-none');
            }
        });

        searchInput.addEventListener('keydown', e => {
            if (e.key === 'Escape') searchDropdown.classList.add('d-none');
        });
    }

    function escHtml(str) {
        return String(str)
            .replace(/&/g, '&amp;').replace(/</g, '&lt;')
            .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
    }

    // ── Form validation ───────────────────────────────────────────────────────
    document.querySelectorAll('form').forEach(form => {
        form.addEventListener('submit', e => {
            let valid = true;
            form.querySelectorAll('input:not([type="search"]):not([type="hidden"]):not([type="file"]), textarea').forEach(input => {
                if (input.hasAttribute('required') && !input.value.trim()) {
                    input.classList.add('is-invalid');
                    valid = false;
                } else {
                    input.classList.remove('is-invalid');
                }
            });
            if (!valid) e.preventDefault();
        });
        form.querySelectorAll('input, textarea').forEach(input => {
            input.addEventListener('input', () => {
                if (input.value.trim()) input.classList.remove('is-invalid');
            });
        });
    });
});
