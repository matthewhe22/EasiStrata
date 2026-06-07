var invoice_id

$("#btn_cancel").click(function () {
    var names = [];
    $("input:checkbox:checked").each(function () {
        names.push(this.value)

    })

    // location.reload();

    $.ajax({
        type: "POST",
        url: '/finance/invoice/cancel',
        data: {
            'names': names,
            'csrfmiddlewaretoken': '{{csrf_token}}',

        },
        success: function (data) {   // `data` is the return of the `load_cities` view function
        location.reload()
            // replace the contents of the city input with the data that came from the server
        }


    });

});

$("#btn_pay").click(function () {
    var names = [];
    $("input:checkbox:checked").each(function () {
        names.push(this.value)

    })

    // location.reload();

    $.ajax({
        type: "POST",
        url: '/finance/invoice/fullpay',
        data: {
            'names': names,
            'csrfmiddlewaretoken': '{{csrf_token}}',

        },
         success: function (data) {   // `data` is the return of the `load_cities` view function
        location.reload()
            // replace the contents of the city input with the data that came from the server
        }


    });

});
// for modal showup and close
$('.btn-info').click(function () {
    invoice_id = $(this).val();
    $('#modal').modal({
        show: true,
        keyboard: true
    });

    $.ajax({
        type: 'GET',// initialize an AJAX request
        url: '/finance/invoice/partpay',                    // set the url of the request (= localhost:8000/hr/ajax/load-cities/)
        data: {
            'invoice_id': invoice_id       // add the country id to the GET parameters
        },
        success: function (data) {   // `data` is the return of the `load_cities` view function
            $("#invoice-num").val(data['invoice']);
            $("#balance").val(data['bal_amount']);
            $("#invoice_id").val(data['invoice_id']);

            // replace the contents of the city input with the data that came from the server
        }
    });
});


$("#pay_save").click(function () {
    var payment_amt = $("#pay_amt").val();
    // var invoice_id = $("#invoice_id").val();

    $('#modal').modal('hide');

    $.ajax({
        type: 'POST',// initialize an AJAX request
        url: '/finance/invoice/partpay',                    // set the url of the request (= localhost:8000/hr/ajax/load-cities/)
        data: {
            'invoice_id': invoice_id,       // add the country id to the GET parameters
            'payment_amt': payment_amt       // add the country id to the GET parameters
        },
        success: function () {   // `data` is the return of the `load_cities` view function
            location.reload();
            // replace the contents of the city input with the data that came from the server
        }
    });
});




