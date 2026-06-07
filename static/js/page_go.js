$("#go").click(function () {
    var total_num = $(".total_page").attr('id');
    total_num = parseInt(total_num);
    var go_page = $("#page_num").val();
    go_page = parseInt(go_page);
    var url_log = window.location.href;
    if (go_page > total_num) {
        go_page = total_num;
    } else if (go_page < 1) {
        go_page = 1;
    }
    var url = new URL(url_log);
    var search_params = url.searchParams;
    search_params.set('page', String(go_page));
    url.search = search_params.toString();
    var new_url = url.toString();
    window.location.replace(url);


})
