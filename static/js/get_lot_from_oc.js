$("#id_oc_ref").change(function () {
    let ocId = $(this).val();
    // alert("ocid is" + ocId);
    update_lot_from_oc(ocId);

});


function update_lot_from_oc(ocId) {

    $.ajax({
        type: 'GET',
        url: '/property/ajax/getlotfromoc',
        data: {
            'ocId': ocId
        },
        success: function (data_lot) {
            $("#id_lot_ref").html(data_lot);
        }
    });

}

