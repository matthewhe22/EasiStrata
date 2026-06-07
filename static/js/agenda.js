$('.del-pri').click(function () {
    let name_id = $(this).attr('name');
    let id = name_id.substring(name_id.indexOf('-') + 1);
    let typeRquest = name_id.substring(0, name_id.indexOf('-'));
    call_del_priority_ajax(id, typeRquest);
    // render_agendas(id);


});

$('.edit').click(function () {
    showAgendaModal();
    let name_id = $(this).attr('name');
    let id = name_id.substring(name_id.indexOf('-') + 1);
    $("#agenda_mode").val("update");
    $("#agenda_id").val(id);
    $.ajax({
        type: 'GET',
        //不定义特殊连接类型
        data: {'id': id},
        url: '/strata/agm/agenda/detail',
        success: function (data) {
            $("#seq_no").prop('disabled', true);
            $("#seq_no").val(data['seq_no']);
            $("#title").val(data['title']);
            $("#modal_content").val(data['content']);


        },
        error: function (data) {
            alert(data['msg']);
        }

    });


})


function call_del_priority_ajax(id, request_type) {
    let request_data = {'agenda_id': id, 'type': request_type};
    $.ajax({
        type: 'POST',
        //不定义特殊连接类型
        data: request_data,
        url: '/strata/agm/agenda/del',
        success: function (data) {
            alert(data['msg']);
            render_agendas(data['agm_id']);

        },
        error: function (data) {
            alert(data['msg']);
        }

    });
}

function showAgendaModal() {
    $("#modal").modal({
        show: true,
        keyboard: true
    });
}