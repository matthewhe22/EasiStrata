const btn_invite = $("#button-id-gen");
const file_upload = $(".custom-file");
const is_init = $("#id_is_init");
const add_motion = $("#add_clause");
const file_label = $("label[for='id_meeting_minutes']");
let update_flag = location.pathname.includes('update');
let id = $("#amg_hidden");
const agenda_table = $("#sub-clause");
const seqNoInput = $("#seq_no");
const titleInput = $("#title");
const contentInput = $("#modal_content");


$(document).ready(function () {
//    check if it is update, if it is then init datetime


    if (update_flag) {
        //logic for update view
        let id = getIdFromUrl();
        btn_invite.show();
        file_upload.show();
        file_label.show();
        $("#amg_hidden").val(id);
        render_agendas(id);
    } else {
        btn_invite.hide();
        file_upload.hide();
        file_label.hide();
        add_motion.hide();
    }
});


is_init.click(
    function () {
        if (is_init.prop('checked')) {
            file_upload.show();
            file_label.show();
            file_upload.prop('required', true);
        } else {
            file_upload.hide();
            file_label.hide();
            file_upload.prop('required', false);
        }


    }
)


$(function () {
    $("#submit-id-submit").on('click', function (e) {
        let agm_form = document.getElementById('agm');
        let form_data = new FormData(agm_form);
        // if it is a updateview , then add id to form data

        if (id.val()) {
            form_data.append('agm_id', id.val());
        }
        $("#agm").submit(function (e) {


            $.ajax({
                type: 'POST',
                cache: false,                                               //上传文件无需缓存
                processData: false,                                          //不对数据做序列化操作
                contentType: false,                                          //不定义特殊连接类型
                data: form_data,
                url: '/strata/agm/ajax/create',
                success: function (data) {
                    alert(data['msg']);
                    if (data['result'] === 'success') {
                        id.val(data['id']);
                        btn_invite.show();
                        add_motion.show();
                        $("#submit-id-submit").hide();

                        render_agendas(data['id']);
                    }
                },
                error: function (data) {
                    alert(data['msg']);
                }
            })
        });
    })
});

btn_invite.click(function () {
    let agm_id = $("#amg_hidden").val();
    if (agm_id) {
        $.ajax({
            type: 'POST',
            //不定义特殊连接类型
            data: {'agm_id': agm_id},
            url: '/strata/agm/ajax/invite',
            success: function (data) {
                alert(data['msg']);
                window.location.replace("/strata/agm/");

            },
            error: function (data) {
                alert(data['msg']);
            }

        });
    } else {
        alert("Error, no AGM ID identified")
    }
});


function render_agendas(agm_id) {
    if (agm_id) {
        $.ajax({
            type: 'GET',
            //不定义特殊连接类型
            data: {'agm_id': agm_id},
            url: '/strata/agm/agenda',
            success: function (data) {
                agenda_table.html(data)

            },
            error: function (data) {
                alert(data['msg']);
            }

        });
    } else {
        alert("Error, no AGM ID identified");
    }
}


$("#agenda_save").click(function () {
    let agmId = 0;
    let seq = seqNoInput.val();
    let title = titleInput.val();
    let content = contentInput.val();
    if (update_flag) {
        agmId = getIdFromUrl();
    } else {
        agmId = id.val();
    }
    let mode = $("#agenda_mode").val();
    let agendaId = $("#agenda_id").val();
    let data = {
        'seq': seq,
        'title': title,
        'content': content,
        'agmId': agmId,
        'mode': mode,
        'agendaId': agendaId
    }

    $.ajax({
        type: 'POST',
        //不定义特殊连接类型
        data: data,
        url: '/strata/agm/agenda/manage',
        success: function (data) {
            alert(data['msg']);
            render_agendas(agmId);

            },
            error: function (data) {
                alert(data['msg']);
            }

        });


    }
)

function getIdFromUrl() {
    let id_index = location.pathname.indexOf('update/');
    id_index = id_index + 7;
    let id = location.pathname.substring(id_index);
    return id;

}


$('#add_clause').click(function () {
    showAgendaModal();
    seqNoInput.prop('disabled', false);
    seqNoInput.val('');
    $("#agenda_mode").val("new");
    $("#agenda_id").val("");
    titleInput.val('');
    contentInput.val('');


})
