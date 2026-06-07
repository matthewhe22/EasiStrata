// used for example purposes
$(document).ready(function () {
    var ctx_live = document.getElementById("myPieChart");
    var myChart = new Chart(ctx_live, {
        type: 'doughnut',
        data: {
            labels: [],
            datasets: [{
                data: [],
                backgroundColor: ['#4e73df', '#1cc88a', '#36b9cc','#1abc9c','#34495e','#3e95cd', "#8e5ea2","#3cba9f","#e8c3b9","#c45850"],
                // hoverBackgroundColor: ['#2e59d9', '#17a673', '#2c9faf'],

            }]
        },
        options: {
            maintainAspectRatio: false,
            tooltips: {
                backgroundColor: "rgb(255,255,255)",
                bodyFontColor: "#858796",
                borderColor: '#dddfeb',
                borderWidth: 1,
                xPadding: 15,
                yPadding: 15,
                displayColors: false,
                caretPadding: 10,
            },
            legend: {
                display: false
            },

        }
    });


// logic to get new data
    var getData = function () {
        $.ajax({
            url: '/base/ajax/get_pie',
            success: function (data) {
                // process your data to pull out what you plan to use to update the chart
                // e.g. new label and a new data point
                console.log(data)

                // add new label and data point to chart's underlying data structures
                myChart.data.labels=data.labels;
                myChart.data.datasets[0].data=data.data;

                // re-render the chart
                myChart.update();
            }
        });
    };

    getData()
    setInterval(getData, 30000);

})


// create initial empty chart
