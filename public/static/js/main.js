document.addEventListener('DOMContentLoaded', () => {

    const voteWidgets = document.querySelectorAll('.vote-widget');

    voteWidgets.forEach(widget => {
        const upBtn = widget.querySelector('.up');
        const downBtn = widget.querySelector('.down');
        const countSpan = widget.querySelector('.vote-count');

        let count = parseInt(countSpan.textContent);
        let userVote = 0;

        const updateUI = (newVote) => {

            if (userVote === newVote) {
                userVote = 0;
            } else {
                userVote = newVote;
            }


            countSpan.textContent = count + userVote;

            upBtn.classList.toggle('active', userVote === 1);
            downBtn.classList.toggle('active', userVote === -1);
        };

        upBtn.addEventListener('click', () => updateUI(1));
        downBtn.addEventListener('click', () => updateUI(-1));
    });


    // --- 2. УЛУЧШЕННАЯ ВАЛИДАЦИЯ ФОРМ ---
    const forms = document.querySelectorAll('form');

    forms.forEach(form => {
        form.addEventListener('submit', (e) => {
            let isValid = true;

            // Берем все текстовые поля, email и пароли
            const inputs = form.querySelectorAll('input:not([type="search"]), textarea');

            inputs.forEach(input => {
                // Если у поля есть атрибут required и оно пустое
                if (input.hasAttribute('required') && !input.value.trim()) {
                    input.classList.add('is-invalid');
                    isValid = false;
                } else {
                    input.classList.remove('is-invalid');
                }
            });

            if (!isValid) {
                e.preventDefault(); // Останавливаем отправку
                console.log('Форма заполнена некорректно');
            }
        });

        // Чтобы красная рамка исчезала сразу, как только пользователь начал вводить текст
        form.querySelectorAll('input, textarea').forEach(input => {
            input.addEventListener('input', () => {
                if (input.value.trim().length > 0) {
                    input.classList.remove('is-invalid');
                }
            });
        });
    });

    const askBtn = document.querySelector('.btn-success');
    if (askBtn) {
        setTimeout(() => {
            askBtn.style.transition = 'transform 0.3s ease';
        }, 100);
    }
});