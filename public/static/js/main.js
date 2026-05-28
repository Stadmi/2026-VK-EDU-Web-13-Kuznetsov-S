document.addEventListener('DOMContentLoaded', () => {

    function getCsrfToken() {
        const cookie = document.cookie.split(';').find(c => c.trim().startsWith('csrftoken='));
        return cookie ? decodeURIComponent(cookie.split('=')[1]) : '';
    }

    function postJson(url, body) {
        return fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken(),
            },
            body: JSON.stringify(body),
        }).then(res => res.json());
    }

    // Vote widgets (questions & answers)
    document.querySelectorAll('.vote-widget').forEach(widget => {
        const type = widget.dataset.type;
        const id = parseInt(widget.dataset.id, 10);
        const upBtn = widget.querySelector('.vote-btn.up');
        const downBtn = widget.querySelector('.vote-btn.down');
        const countSpan = widget.querySelector('.vote-count');

        if (!upBtn || !downBtn) return;

        function handleVote(value) {
            const url = type === 'question' ? '/vote/question/' : '/vote/answer/';
            postJson(url, { id, value })
                .then(data => {
                    if (data.error) {
                        if (data.redirect) {
                            window.location.href = data.redirect;
                            return;
                        }
                        const msg = typeof data.error === 'string' ? data.error : JSON.stringify(data.error);
                        alert('Ошибка: ' + msg);
                        return;
                    }
                    countSpan.textContent = data.rating;
                    upBtn.classList.toggle('active', data.user_vote === 1);
                    downBtn.classList.toggle('active', data.user_vote === -1);
                })
                .catch(() => alert('Ошибка соединения. Попробуйте позже.'));
        }

        upBtn.addEventListener('click', () => handleVote(1));
        downBtn.addEventListener('click', () => handleVote(-1));
    });

    // Mark correct answer buttons
    document.querySelectorAll('.mark-correct-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const answerId = parseInt(btn.dataset.answerId, 10);
            postJson('/mark-correct/', { answer_id: answerId })
                .then(data => {
                    if (data.error) {
                        if (data.redirect) {
                            window.location.href = data.redirect;
                            return;
                        }
                        alert('Ошибка: ' + data.error);
                        return;
                    }
                    // Update all answer cards on the page
                    document.querySelectorAll('.mark-correct-btn').forEach(b => {
                        const isThis = parseInt(b.dataset.answerId, 10) === data.answer_id;
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
                .catch(() => alert('Ошибка соединения. Попробуйте позже.'));
        });
    });

    // Form validation
    document.querySelectorAll('form').forEach(form => {
        form.addEventListener('submit', e => {
            let isValid = true;
            form.querySelectorAll('input:not([type="search"]):not([type="hidden"]):not([type="file"]), textarea').forEach(input => {
                if (input.hasAttribute('required') && !input.value.trim()) {
                    input.classList.add('is-invalid');
                    isValid = false;
                } else {
                    input.classList.remove('is-invalid');
                }
            });
            if (!isValid) e.preventDefault();
        });

        form.querySelectorAll('input, textarea').forEach(input => {
            input.addEventListener('input', () => {
                if (input.value.trim().length > 0) input.classList.remove('is-invalid');
            });
        });
    });
});
