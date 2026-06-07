$("#new_request").click(function () {


    showUploadModal();


})

$("#btnSubmit").click(function () {
    let form_data = $("#request_form").serialize();

    $.ajax({
        type: 'POST',
        dataType: 'JSON',
        // cache: false,                                               //上传文件无需缓存
        // processData: false,                                          //不对数据做序列化操作
        // contentType: false,                                          //不定义特殊连接类型
        data: form_data,
        url: '/strata/owner/request/new',
        success: function (data) {
            alert(data['msg']);
            hideUploadModal();
            location.reload();

        },
        error: function (data) {
            alert(data['msg']);
        }
    })

})


function showUploadModal() {
    $("#uploadModal").modal({
        show: true,
        keyboard: true
    });
}


function hideUploadModal() {

    $("#uploadModal").modal('hide');
}

