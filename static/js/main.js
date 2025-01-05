document.addEventListener('DOMContentLoaded', function() {
    // 监听所有表单提交
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            console.log('Form submission intercepted');
            // 不阻止表单提交
        });
    });
});
