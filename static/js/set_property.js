$(document).ready(function () {
    let ocId = $("#id_oc_ref :selected").val();
    let lotId = $("#id_lot_ref :selected").val();


       // console.log(ocId)// get the selected country ID from the HTML input
    $.ajax({
        type: 'GET',// initialize an AJAX request
        url: '/property/ajax/getproperty',                    // set the url of the request (= localhost:8000/hr/ajax/load-cities/)
        data: {
            'ocId': ocId       // add the country id to the GET parameters
        },
        success: function (data) {   // `data` is the return of the `load_cities` view function
            var property_id = data.property;
            var liability = data.liability;
            $("#id_property").find('option[value=' + property_id + ']').attr('selected', true);
            $("#id_total_liability").val(liability);
            // replace the contents of the city input with the data that came from the server
        }
    });

    $.ajax({
        type: 'GET',// initialize an AJAX request
        url: '/property/ajax/getlotfromoc',                    // set the url of the request (= localhost:8000/hr/ajax/load-cities/)
        data: {
            'ocId': ocId,
            'lotId': lotId
        },
        success: function (data) {   // `data` is the return of the `load_cities` view function
            $("#id_lot_ref").html(data);  // replace the contents of the city input with the data that came from the server
        }
    });


});

