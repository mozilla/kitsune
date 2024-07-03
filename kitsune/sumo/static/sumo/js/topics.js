document.addEventListener('DOMContentLoaded', function () {
    var dropdown = document.getElementById('products-topics-dropdown');
    dropdown.addEventListener('change', function () {
        let selectedUrl = this.value;
        if (selectedUrl) {
            window.location.href = selectedUrl;
        }
    });
});