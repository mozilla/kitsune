window.addEventListener("DOMContentLoaded", (event) => {
    const geoIPUrl = 'https://location.services.mozilla.com/v1/country?key=fa6d7fc9-e091-4be1-b6c1-5ada5815ae9d';
    const countryField = document.querySelector('input#id_country');

    if (countryField) {
        fetch(geoIPUrl)
        .then(response => {
            if (!response.ok) {
                throw new Error(`Fetch failed, status ${response.status}`)
            }
            return response.json();

        })
        .then(data => {
            countryField.value = data.country_name;
        })
    }
});
