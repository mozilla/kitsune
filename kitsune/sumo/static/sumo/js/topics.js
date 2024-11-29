document.addEventListener('DOMContentLoaded', function () {
    let dropdown = document.getElementById('products-topics-dropdown');
    if (dropdown) {
        dropdown.addEventListener('change', function () {
            let selectedUrl = this.value;
            if (selectedUrl) {
                window.location.href = selectedUrl;
            }
        });
    }
});
