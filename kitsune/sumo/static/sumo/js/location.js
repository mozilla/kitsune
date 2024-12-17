window.addEventListener("DOMContentLoaded", (event) => {
    // const geoIPUrl = 'https://location.services.mozilla.com/v1/country?key=fa6d7fc9-e091-4be1-b6c1-5ada5815ae9d';
    const proxyUrl = "/questions/mozilla/location/"
    const countryField = document.querySelector('input#id_country');

    if (countryField) {
        fetch(proxyUrl)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`Fetch failed, status ${response.status}`)
                }
                return response.json();

            })
            .then(data => {

                if (data && data.country_name) {
                    countryField.value = data.country_name;
                } else {
                    countryField.value = '';
                }
            })
            .catch(error => {
                console.error('Error fetching country:', error);
                countryField.value = '';
            });
    }
});
