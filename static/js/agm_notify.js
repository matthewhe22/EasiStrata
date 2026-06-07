const id = $("#upload-id")
$(".fa-send").click(function () {
    let agm_id = $(this).attr("id");

    agm_id = agm_id.substring(5);


    $.ajax({
        type: 'POST',
        //不定义特殊连接类型
        data: {'agm_id': agm_id},
        url: '/strata/agm/ajax/sendinvite',
        success: function (data) {
            alert(data['msg']);

        },
        error: function (data) {
            alert(data['msg']);
        }


    });
});


$(".deletelink").click(function () {
    let agm_id = $(this).attr("id");
    agm_id = agm_id.substring(4);
    $.ajax({
        type: 'POST',
        //不定义特殊连接类型
        data: {'agm_id': agm_id},
        url: '/strata/agm/ajax/del',
        success: function (data) {
            alert(data['msg']);
            location.reload();

        },
        error: function (data) {
            alert(data['msg']);
        }


    });


})


$(".agm-upload").click(function () {
    let agm_id = $(this).attr("id");
    agm_id = agm_id.substring(5);
    id.val(agm_id);

    showUploadModal();


})

$("#btnUpload").click(function () {
    // console.log('upload being triggered');
    let agm_form = document.getElementById('minutesUpload');
    let form_data = new FormData(agm_form);

    // if it is a updateview , then add id to form data

    // if (id.val()) {
    //     form_data.append('agm_id', id.val());
    // }
    $.ajax({
        type: 'POST',
        cache: false,                                               //上传文件无需缓存
        processData: false,                                          //不对数据做序列化操作
        contentType: false,                                          //不定义特殊连接类型
        data: form_data,
        url: '/strata/agm/ajax/minutes',
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

