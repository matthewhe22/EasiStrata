
$("#in_clientCode").change(function() {
    // this will fire when #select1 change event has finished updating the options.
    $("#in_fundcode").children().hide();
    $("#in_fundcode").children("option[value=0]").show();
    console.log($(this).val())
    $("#in_fundcode").children("option[class^=fc_" + $(this).val() + "]").show()
});

$("#submit_form").submit(function(event) {
    if ($("#in_clientCode").val()==0 || $("#in_fundcode").val()==0) {
        alert("Choose both Client and Fund Code");
        event.preventDefault();
        // return false
    }
});
