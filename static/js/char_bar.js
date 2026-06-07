// used for example purposes
$(document).ready(function () {
    var ctx_live = document.getElementById("myAreaChart");
    var myChart = new Chart(ctx_live, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                data: [],
                label: "Management Revenue",
                lineTension: 0.3,
                backgroundColor: "rgba(78, 115, 223, 0.05)",
                borderColor: "rgba(78, 115, 223, 1)",
                pointRadius: 3,
                pointBackgroundColor: "rgba(78, 115, 223, 1)",
                pointBorderColor: "rgba(78, 115, 223, 1)",
                pointHoverRadius: 3,
                pointHoverBackgroundColor: "rgba(78, 115, 223, 1)",
                pointHoverBorderColor: "rgba(78, 115, 223, 1)",
                pointHitRadius: 10,
                pointBorderWidth: 2,
            }]
        },
        options: {
            maintainAspectRatio: false,
            layout: {
                padding: {
                    left: 10,
                    right: 25,
                    top: 25,
                    bottom: 0
                }
            },
            scales: {
                xAxes: [{
                    time: {
                        unit: 'date'
                    },
                    gridLines: {
                        display: false,
                        drawBorder: false
                    },
                    ticks: {
                        maxTicksLimit: 7
                    }
                }],
                yAxes: [{
                    ticks: {
                        maxTicksLimit: 5,
                        padding: 10,
                        // // Include a dollar sign in the ticks
                        // callback: function (value, index, values) {
                        //     return '$' + number_format(value);
                        // }
                    },
                    gridLines: {
                        color: "rgb(234, 236, 244)",
                        zeroLineColor: "rgb(234, 236, 244)",
                        drawBorder: false,
                        borderDash: [2],
                        zeroLineBorderDash: [2]
                    }
                }],
            },
            legend: {
                display: false
            },
            tooltips: {
                backgroundColor: "rgb(255,255,255)",
                bodyFontColor: "#858796",
                titleMarginBottom: 10,
                titleFontColor: '#6e707e',
                titleFontSize: 14,
                borderColor: '#dddfeb',
                borderWidth: 1,
                xPadding: 15,
                yPadding: 15,
                displayColors: false,
                intersect: false,
                mode: 'index',
                caretPadding: 10,

            }
        }
    });

// logic to get new data
    var getData = function () {
        $.ajax({
            url: '/base/ajax/get_rev',
            success: function (data) {
                // process your data to pull out what you plan to use to update the chart
                // e.g. new label and a new data point

                // add new label and data point to chart's underlying data structures
                myChart.data.labels = data.labels;
                myChart.data.datasets[0].data = data.data;

                // re-render the chart
                myChart.update();
            }
        });
    };
    getData()
    setInterval(getData, 30000);

})


// create initial empty chart
