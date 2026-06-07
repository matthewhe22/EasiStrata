$("#clear").click(function () {
    var pathname = window.location.pathname; // Returns path only (/path/example.html)
    var url = window.location.href;     // Returns full URL (https://example.com/path/example.html)
    var origin = window.location.origin;
    var beforeUrl = url.substr(0, url.indexOf("?"));
    console.log(beforeUrl);
    window.navigate(beforeUrl);
    // window.location.replace(beforeUrl);

    // return false

})
