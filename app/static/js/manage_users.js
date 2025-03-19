document.addEventListener('DOMContentLoaded', function() {
    // Обработка нажатия на кнопку "Обновить данные"
    document.querySelectorAll('.update-credentials').forEach(button => {
        button.addEventListener('click', function() {
            const userId = this.getAttribute('data-user-id');
            fetch(`/update_user_credentials/${userId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Показываем новые данные
                    const credentialsDiv = document.getElementById(`credentials-${userId}`);
                    credentialsDiv.style.display = 'block';
                    document.getElementById(`username-${userId}`).textContent = data.username;
                    document.getElementById(`password-${userId}`).textContent = data.password;
                }
            })
            .catch(error => {
                console.error('Ошибка:', error);
            });
        });
    });
});

function copyToClipboard(text) {
navigator.clipboard.writeText(text).then(() => {
    alert('Данные скопированы в буфер обмена!');
}).catch(err => {
    console.error('Ошибка при копировании:', err);
});
}

document.addEventListener('DOMContentLoaded', function() {
document.querySelectorAll('.update-credentials').forEach(button => {
    button.addEventListener('click', function() {
        const userId = this.getAttribute('data-user-id');
        fetch(`/update_user_credentials/${userId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const credentialsDiv = document.getElementById(`credentials-${userId}`);
                credentialsDiv.style.display = 'block';
                credentialsDiv.innerHTML = `
                    <strong>Новые данные:</strong>
                    <div>Логин: <span id="username-${userId}">${data.username}</span></div>
                    <div>Пароль: <span id="password-${userId}">${data.password}</span></div>
                    <button class="btn btn-sm btn-secondary mt-2" onclick="copyToClipboard('${data.username}')">Копировать логин</button>
                    <button class="btn btn-sm btn-secondary mt-2" onclick="copyToClipboard('${data.password}')">Копировать пароль</button>
                `;
            }
        })
        .catch(error => {
            console.error('Ошибка:', error);
        });
    });
});
});