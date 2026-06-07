$("#id_oc_ref").change(function () {
    var oc_id = $(this).val();  // get the selected country ID from the HTML input

    $.ajax({
        type: 'GET',// initialize an AJAX request
        url: '/property/ajax/getliability',                    // set the url of the request (= localhost:8000/hr/ajax/load-cities/)
        data: {
            'oc_id': oc_id       // add the country id to the GET parameters
        },
        success: function (data) {   // `data` is the return of the `load_cities` view function
            var liability = data.liability
            $("#id_total_liability").val(liability);  // replace the contents of the city input with the data that came from the server
        }
    });


});

