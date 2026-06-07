$(document).ready(function(){
    $("#id_street").keyup(function(){
          var street = $("#id_street").val();
          $("#id_name").val(street);
    });
});