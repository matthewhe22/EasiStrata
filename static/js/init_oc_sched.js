$("#oc_init").click(function () {
    $.ajax({
        type: 'POST',//
        url: '/base/ajax/oc_sched_init',

        success: function (data) {   // `data` is the return of the `load_cities` view function
            console.log(data['result'])
            location.reload()
            // replace the contents of the city input with the data that came from the server
        }
    });
});
