$("#recon").click(function () {
    var names = [];
    $("input:checkbox:checked").each(function () {
        names.push(this.value)

    })
    $.ajax({
        type: "POST",
        url: '/finance/gl/recon',
        data: {
            'names': names,
            'csrfmiddlewaretoken': '{{csrf_token}}',
            'type':'recon'

        },success: function () {   // `data` is the return of the `load_cities` view function
        location.reload()
            // replace the contents of the city input with the data that came from the server
        }
    });
});



$("#present").click(function () {
    var names = [];
    $("input:checkbox:checked").each(function () {
        names.push(this.value)

    })
    $.ajax({
        type: "POST",
        url: '/finance/gl/recon',
        data: {
            'names': names,
            'csrfmiddlewaretoken': '{{csrf_token}}',
            'type':'present'

        },success: function () {   // `data` is the return of the `load_cities` view function
        location.reload()
            // replace the contents of the city input with the data that came from the server
        }
    });
});

// function for modal show and close TODO for partial recon to be changed

$(".btn-info").click(function () {
    invoice_id = $(this).val();
    console.log(invoice_id)
    $("#modal").modal({
        show: true,
        keyboard: true
    });

    $.ajax({
        type: 'GET',// initialize an AJAX request
        url: '/finance/billing/partpay',                    // set the url of the request (= localhost:8000/hr/ajax/load-cities/)
        data: {
            'invoice_id': invoice_id       // add the country id to the GET parameters
        },
        success: function (data) {   // `data` is the return of the `load_cities` view function
            $("#invoice-num").val(data['invoice']);
            $("#balance").val(data['bal_amount']);
            $("#invoice_id").val(data['invoice_id']);
            location.reload()
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
        url: '/finance/billing/partpay',                    // set the url of the request (= localhost:8000/hr/ajax/load-cities/)
        data: {
            'invoice_id': invoice_id,       // add the country id to the GET parameters
            'payment_amt': payment_amt       // add the country id to the GET parameters
        },
        success: function (data) {   // `data` is the return of the `load_cities` view function
        location.reload()
            // replace the contents of the city input with the data that came from the server
        }
    });
});


$("#all").click(function () {
    $(".form-check-input").prop('checked', $(this).prop('checked'));
});