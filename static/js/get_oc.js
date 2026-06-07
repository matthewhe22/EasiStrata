$("#id_property").change(function () {
    let propertyId = $(this).val();

    update_oc(propertyId);
    update_lot(propertyId);

});


$("#id_property_ref").change(function () {
    let propertyId = $(this).val();

    update_oc(propertyId);
    update_lot(propertyId);

});

// $("#id_oc_ref").change(function () {
//     let ocId = $(this).val();
//     alert("ocid is" + ocId);
//     update_lot_from_oc(ocId);
//
// });


function update_oc(propertyId) {

    $.ajax({
        type: 'GET',// initialize an AJAX request
        url: '/property/ajax/getoc',                    // set the url of the request (= localhost:8000/hr/ajax/load-cities/)
        data: {
            'propertyId': propertyId
        },
        success: function (data_oc) {
            $("#id_oc_ref").html(data_oc);
        }
    });

}

function update_lot(propertyId) {

    $.ajax({
        type: 'GET',
        url: '/property/ajax/getlot',
        data: {
            'propertyId': propertyId
        },
        success: function (data_lot) {
            $("#id_lot_ref").html(data_lot);
        }
    });

}


// function update_lot_from_oc(ocId) {
//
//     $.ajax({
//         type: 'GET',
//         url: '/property/ajax/getlotfromoc',
//         data: {
//             'ocId': ocId
//         },
//         success: function (data_lot) {
//             $("#id_lot_ref").html(data_lot);
//         }
//     });
//
// }
//
