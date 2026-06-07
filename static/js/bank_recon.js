$("#recon").click(function () {
    let names = [];
    $("input:checkbox:checked").each(function () {
        names.push(this.value)

    })
    $.ajax({
        type: "POST",
        url: '/finance/bank/recon',
        data: {
            'names': names,
            'csrfmiddlewaretoken': '{{csrf_token}}',
            'type': 'recon'

        }, success: function () {
            location.reload()

        }
    });
});


$("#present").click(function () {
    let names = [];
    $("input:checkbox:checked").each(function () {
        names.push(this.value)

    })
    $.ajax({
        type: "POST",
        url: '/finance/bank/recon',
        data: {
            'names': names,
            'csrfmiddlewaretoken': '{{csrf_token}}',
            'type': 'present'

        }, success: function () {
            location.reload()
        }
    });
});

$("#openBankModal").click(function () {


    $("#modal_import").modal({
        show: true,
        keyboard: true
    });


});

$("#bank_upload").click(function () {
    let data = new FormData($("#bankAttachment").get(0));
    $.ajax({
        processData: false,
        contentType: false,
        type: "POST",
        url: '/finance/bank/upload',
        data: data,
        success: function () {
            alert('success');
        }
    });
});


//click event for cash receipt button
$(".cash").click(function () {
    let id_list = $(this).val().split("-");
    let cashID = id_list[0];
    let ocID = id_list[1];
    $("#bank_trans_id").val(cashID);
    $("#modal_cash").modal({
        show: true,
        keyboard: true
    });

    $.ajax({
        type: 'GET',// initialize an AJAX request
        url: '/property/ajax/getlotfromoc',
        data: {
            'ocId': ocID
        },
        success: function (data) {   // `data` is the return of the `load_cities` view function
            $("#id_lot_ref").html(data);
            // replace the contents of the city input with the data that came from the server
        },
        error: function () {
            alert("fail to get lot dropdown list from OC ID")

        }
    });
    $.ajax({
        type: 'GET',// initialize an AJAX request
        url: '/finance/ajax/getbanktrans',
        data: {
            'cashID': cashID
        },
        success: function (data) {
            $("#balance").val(data['balance']);

        }
    });
});


$("#cash_submit").click(function () {

    let balance = $("#balance").val();
    let form_data = {
        'amount': parseFloat($("#amount").val()),
        'desc': $("#desc").val(),
        'ref': $("#ref").val(),
        'lot_id': $("#id_lot_ref").val(),
        'bank_id': $("#bank_trans_id").val()
    };
    if (Math.abs(form_data.amount) > Math.abs(balance) || form_data.amount === 0) {
        alert("you assign greater amount than balance or amount can't be 0");

    } else if ($("#id_lot_ref").val() == null) {
        alert("Lot field can't be null");
    } else {
        $.ajax({
            type: 'POST',//
            url: '/finance/ajax/manualcash',
            data: form_data,
            success: function (data) {
                alert(data['msg']);

            },
            error: function (data) {
                alert(data['msg']);
            }
        });
        $('#modal_cash').modal('hide');

    }


})