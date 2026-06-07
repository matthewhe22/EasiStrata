$(".btn-warning").click(function () {
    var msg = $(this).val();

    location.reload();
    $.ajax({
        type: 'POST',// initialize an AJAX request
        url: '/base/ajax/read_alert',                    // set the url of the request (= localhost:8000/hr/ajax/load-cities/)
        data: {
            'msg': msg       // add the country id to the GET parameters
        },
        success: function (data) {   // `data` is the return of the `load_cities` view function
        location.reload()
            // replace the contents of the city input with the data that came from the server
        }
    });


});

