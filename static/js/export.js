$(function () {
    $("#export").click(function () {
        //step1, get the parameter
        var ocId = $("#id_oc_ref :selected").val();
        var startDate = $("#id_posting_gt").val();
        var toDate = $("#id_posting_lt").val();

        $.ajax({
            url: '/finance/gl/export',
            type: 'POST',
            data: {
                'ocID': ocId,
                'startDate': startDate,
                'toDate': toDate

            },

            success: function (data) {
                let filename = data['filename'];
                open(filename);


            },
            error: function (data) {
                alert("error");

            }

        })


    })

})