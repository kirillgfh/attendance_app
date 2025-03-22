document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.update-credentials').forEach(button => {
        button.addEventListener('click', function() {
            console.log('click');
            const userId = this.getAttribute('data-user-id');
            const credentialsDiv = document.getElementById(`credentials-${userId}`);
            const loadingDiv = document.getElementById(`loading-${userId}`);
            const dataDiv = document.getElementById(`data-${userId}`);

            // Показываем блок с данными и анимацию загрузки
            credentialsDiv.style.display = 'block';
            loadingDiv.style.display = 'block';
            dataDiv.style.display = 'none';

            fetch(`/update_user_credentials/${userId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Скрываем анимацию загрузки и показываем данные
                    loadingDiv.style.display = 'none';
                    dataDiv.style.display = 'block';

                    // Обновляем данные и кнопки
                    dataDiv.innerHTML = `
                        <div>Логин: <span id="username-${userId}">${data.username}</span></div>
                        <div>Пароль: <span id="password-${userId}">${data.password}</span></div>
                        <button class="btn btn-sm btn-secondary mt-2" onclick="copyToClipboard('${data.username}')">Копировать логин</button>
                        <button class="btn btn-sm btn-secondary mt-2" onclick="copyToClipboard('${data.password}')">Копировать пароль</button>
                    `;
                }
            })
            .catch(error => {
                console.error('Ошибка:', error);
                // В случае ошибки скрываем анимацию загрузки и показываем сообщение об ошибке
                loadingDiv.style.display = 'none';
                credentialsDiv.innerHTML = '<div class="text-danger">Ошибка при обновлении данных</div>';
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