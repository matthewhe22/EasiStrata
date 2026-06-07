// $(document).ready(function () {
//     $(".detail").click(function () {
//         // console.log($(this).attr('id'));
//         var id=$(this).attr('id');
//         var values=new Array();
//         values=id.split('-');
//         var url="/property/ocbudget/?property_id="+values[1]+"&fin_year="+values[0];
//         window.location.href=url;
//
//
//     });
// })


$(".detail").click(function () {
    // console.log($(this).attr('id'));
    var id = $(this).attr('id');
    let values = id.split('-');
    var url = "/property/ocbudget/?property_id=" + values[1] + "&fin_year=" + values[0];
    window.location.href = url;


});


$('#new_budget').click(function () {
    // invoice_id = $(this).val();
    $('#modal').modal({
        show: true,
        keyboard: true
    });
});

$("#budget_save").click(function () {

    let ocId = $("#id_oc_ref :selected").val();
    let finYear = $("#fin_year").val();
    // var invoice_id = $("#invoice_id").val();

    $('#modal').modal('hide');

    $.ajax({
        type: 'POST',// initialize an AJAX request
        url: '/property/ocbudget/copy',
        data: {
            'oc_id': ocId,
            'fin_year': finYear
        },
        success: function (data) {
            let message = data['message'];
            let result = data['result'];

            alertManage(result, message);
            // subject to change to notification
            // location.reload();
        }
    });
});