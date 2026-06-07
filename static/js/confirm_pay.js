var invoice_id;

function getSlectedRecords() {

    let records = [];
    $("input:checkbox:checked").each(function () {
        records.push(this.value)

    });
    return records;


}


// button full payment click function

$("#btn_pay").click(function () {
    let names = getSlectedRecords();

    $.ajax({
        type: "POST",
        url: '/finance/billing/confirm',
        data: {
            'names': names,
            'csrfmiddlewaretoken': '{{csrf_token}}',

        }, success: function () {   // `data` is the return of the `load_cities` view function
            location.reload()
            // replace the contents of the city input with the data that came from the server
        }
    });
});


$("#resend").click(function () {
    let names = getSlectedRecords();

    $.ajax({
        type: "POST",
        url: '/finance/billing/resend',
        data: {
            'names': names,
            'csrfmiddlewaretoken': '{{csrf_token}}',

        }, success: function () {   // `data` is the return of the `load_cities` view function
            alert("items selected have been resent!");
            location.reload()
            // replace the contents of the city input with the data that came from the server
        }
    });
});


$("#reset").click(function () {
    console.log("click reset button");
    let names = [];
    $("input:checkbox:checked").each(function () {
        names.push(this.value)

    });
    $.ajax({
        type: "POST",
        url: '/finance/billing/reset',
        data: {
            'names': names,
            'csrfmiddlewaretoken': '{{csrf_token}}',

        }, success: function () {   // `data` is the return of the `load_cities` view function
            location.reload();
            alert("payments for selected billing have been reversed");
            // replace the contents of the city input with the data that came from the server
        }
    });
});


// invoice partial payment function

$(".btn-info").click(function () {
    invoice_id = $(this).val();
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

            // replace the contents of the city input with the data that came from the server
        }
    });
});

// reminder modal function- open the remind modal

$("#btn_remind").click(function () {


    $("#modal_reminder").modal({
        show: true,
        keyboard: true
    });


});

// reminder ajax get value and render ajax request
$("#remind_send").click(function () {
    let billList = getSlectedRecords();
    let body = $("#remind_body").val();

    $.ajax({
        type: 'POST',// initialize an AJAX request
        url: '/finance/billing/remind',
        data: {
            'billList': billList,
            'body': body
        },
        success: function (data) {
            //TODO change to alert in bootstrap
            alert(data['msg'])


        }
    });

});


// save button in partial payment modal
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

// cancel billing function

$(".cancel").click(function () {
    alert('cancel click');
    let bill_id = $(this).val();

    $.ajax({
        type: 'POST',// initialize an AJAX request
        url: '/finance/ajax/billing/cancel',
        data: {
            'bill_id': bill_id
        },
        success: function (data) {   // `data` is the return of the `load_cities` view function
            alert(data['msg']);

            // replace the contents of the city input with the data that came from the server
        },
        error: function (data) {
            alert(data['msg']);


        }
    });
});