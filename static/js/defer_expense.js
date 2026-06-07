//step1 load document  and check if the expense type got deffered indicator
//step 2 show or hide the defer input based on the income_expenese_value
$(document).ready(function () {
    render_defer_input();
});


$("#id_exp_ref").change(function () {
    render_defer_input();

});


function render_defer_input() {
    let income_expense_id = $("#id_exp_ref").val();
    $.ajax({
        type: 'GET',// initialize an AJAX request
        url: '/finance/ajax/getdefer',
        data: {
            'income_id': income_expense_id
        },
        success: function (data) {
            if (data['ind']) {
                show_defer_inputs();
            } else {
                hide_defer_inputs();
            }
        }
    });

}


function hide_defer_inputs() {
    $('label[for=id_defer_from], input#id_defer_from').hide();
    $('label[for=id_defer_periods], input#id_defer_periods').hide();
    $("#id_defer_from").attr("required", false);
    $("#id_defer_periods").attr("required", false);

}


function show_defer_inputs() {
    $('label[for=id_defer_from], input#id_defer_from').show();
    $('label[for=id_defer_periods], input#id_defer_periods').show();
    $("#id_defer_from").attr("required", true);
    $("#id_defer_periods").attr("required", true);

}