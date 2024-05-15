document.addEventListener('DOMContentLoaded', function () {
    var dropdown = document.getElementById('products-dropdown');
    dropdown.addEventListener('change', function () {
        var selectedUrl = this.value;
        if (selectedUrl) {
            window.location.href = selectedUrl;
        }
    });
});