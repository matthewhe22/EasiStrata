$('.collapse-item').click(function () {
    localStorage.setItem("selected-item", $(this).attr('id'));

});


$(document).ready(function () {
    var id=localStorage.getItem("selected-item")



    $("#"+id).parent().parent().collapse('show')

    $('.collapse-item').removeClass(".collapse-item.active");
    $("#"+id).addClass("hover active");
});
