function showModal(flag) {
    if (flag) {
        $("#modal").modal({
            show: true,
            keyboard: true
        });
    } else {
        $('#modal').modal('toggle');
    }

}


$("#new_fs").click(function () {
    showModal(true);

})


$("#fs_save").click(function () {
    let fs_form = document.getElementById('fs_form');
    let form_data = new FormData(fs_form);

    $.ajax(
        {
            type: 'POST',
            cache: false,                                               //上传文件无需缓存
            processData: false,                                          //不对数据做序列化操作
            contentType: false,                                          //不定义特殊连接类型
            data: form_data,
            url: '/finance/fs/owner',
            success: function (data) {
                alert(data['msg']);
                showModal(false);
                location.reload();
                $("#fs").addClass('active');

            },
            error: function (data) {
                alert(data['msg']);
            }
        }
    )


})


$(".fa-trash").click(function () {
        let id = parseInt(this.id.substr(4));
        console.log(id);
        $.ajax(
            {
                type: "POST",
                data: {"id": id},
                url: '/finance/fs/owner/delete',
                success: function (data) {
                    alert(data['msg']);
                    location.reload();
                    $("#fs").tab(show);


                },
                error: function (data) {
                    alert(data['msg']);
                }

            }
        )

    }
)