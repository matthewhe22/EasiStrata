function getSlectedRecords() {

    let records = [];
    $("input:checkbox:checked").each(function () {
        records.push(this.value)

    });
    return records;


}


// button to cancel the cash receipt

$("#btn_cancel").click(function () {
    let names = getSlectedRecords();

    $.ajax({
        type: "POST",
        url: '/finance/cash/cancel',
        data: {
            'names': names,
            'csrfmiddlewaretoken': '{{csrf_token}}',

        }, success: function (data) {
            alert(data['msg']);
            location.reload()

        }, error: function (data) {
            alert(data['msg']);
            location.reload()

        }
    });
});