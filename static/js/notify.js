$(document).ready(function () {
$.ajax({
    url:"/base/ajax/notify",
    datatype:"html",
    type: "GET",
    success: function(data) {
        $("#mx-1").html(data);
    }
  });
});