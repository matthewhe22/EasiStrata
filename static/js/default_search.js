$(document).ready(function () {
    var search = window.location.search;
    var url = window.location.href
    if (search === "") {
        url = url + "?payment_status=unpaid";
        window.location.replace(url);
    }
});

