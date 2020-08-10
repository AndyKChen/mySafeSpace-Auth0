
document.addEventListener('DOMContentLoaded', () => {
  // Set new default font family and font color to mimic Bootstrap's default styling
Chart.defaults.global.defaultFontFamily = 'Nunito', '-apple-system,system-ui,BlinkMacSystemFont,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif';
Chart.defaults.global.defaultFontColor = '#858796';

// get attribute data 
var attribute_totals = [document.getElementById('1').innerHTML, document.getElementById('2').innerHTML, document.getElementById('3').innerHTML, 
document.getElementById('4').innerHTML, document.getElementById('5').innerHTML, document.getElementById('6').innerHTML, document.getElementById('7').innerHTML];

var attribute_totals = attribute_totals.map(Number)

// get attribute breakdown
var individual_attributes = [document.getElementById('a').innerHTML, document.getElementById('b').innerHTML, document.getElementById('c').innerHTML, 
document.getElementById('d').innerHTML, document.getElementById('e').innerHTML];

var individual_attributes = individual_attributes.map(Number)


// get negative msgs

var negatives = [document.getElementById('8').innerHTML, document.getElementById('9').innerHTML, document.getElementById('10').innerHTML, 
document.getElementById('11').innerHTML, document.getElementById('12').innerHTML, document.getElementById('13').innerHTML, document.getElementById('14').innerHTML];

var negatives = negatives.map(Number)

// get positive msgs

var positives = [document.getElementById('15').innerHTML, document.getElementById('16').innerHTML, document.getElementById('17').innerHTML, 
document.getElementById('18').innerHTML, document.getElementById('19').innerHTML, document.getElementById('20').innerHTML, document.getElementById('21').innerHTML];

var positives = positives.map(Number)    

// get neutral msgs

var neutrals = [document.getElementById('22').innerHTML, document.getElementById('23').innerHTML, document.getElementById('24').innerHTML, 
document.getElementById('25').innerHTML, document.getElementById('26').innerHTML, document.getElementById('27').innerHTML, document.getElementById('28').innerHTML];

var neutrals = neutrals.map(Number)    


// get total messages
var totals = [document.getElementById('f').innerHTML, document.getElementById('g').innerHTML, document.getElementById('h').innerHTML, 
document.getElementById('i').innerHTML, document.getElementById('j').innerHTML, document.getElementById('k').innerHTML, document.getElementById('l').innerHTML];

var totals = totals.map(Number)

//daily sentiment breakdown
sentiment_breakdown = [Number(document.getElementById('14').innerHTML), Number(document.getElementById('21').innerHTML), Number(document.getElementById('28').innerHTML)];

// get graph labels
var labels = [document.getElementById('d1').innerHTML, document.getElementById('d2').innerHTML, document.getElementById('d3').innerHTML, 
document.getElementById('d4').innerHTML, document.getElementById('d5').innerHTML, document.getElementById('d6').innerHTML, document.getElementById('d7').innerHTML];

// Pie Chart Example
var ctx = document.getElementById("myPieChart");
var myPieChart = new Chart(ctx, {
  type: 'doughnut',
  data: {
    labels: ["Toxic", "Insult", "Sexual", "Threat", "Identity Attack"],
    datasets: [{
      data: individual_attributes,
      backgroundColor: ['#4e73df', '#1cc88a', '#36b9cc', 'red', 'pink'],
      hoverBackgroundColor: ['#2e59d9', '#17a673', '#2c9faf', 'red', 'pink'],
      hoverBorderColor: "rgba(234, 236, 244, 1)",
    }],
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
    cutoutPercentage: 60,
  },
});

function number_format(number, decimals, dec_point, thousands_sep) {
    // *     example: number_format(1234.56, 2, ',', ' ');
    // *     return: '1 234,56'
    number = (number + '').replace(',', '').replace(' ', '');
    var n = !isFinite(+number) ? 0 : +number,
      prec = !isFinite(+decimals) ? 0 : Math.abs(decimals),
      sep = (typeof thousands_sep === 'undefined') ? ',' : thousands_sep,
      dec = (typeof dec_point === 'undefined') ? '.' : dec_point,
      s = '',
      toFixedFix = function(n, prec) {
        var k = Math.pow(10, prec);
        return '' + Math.round(n * k) / k;
      };
    // Fix for IE parseFloat(0.55).toFixed(0) = 0;
    s = (prec ? toFixedFix(n, prec) : '' + Math.round(n)).split('.');
    if (s[0].length > 3) {
      s[0] = s[0].replace(/\B(?=(?:\d{3})+(?!\d))/g, sep);
    }
    if ((s[1] || '').length < prec) {
      s[1] = s[1] || '';
      s[1] += new Array(prec - s[1].length + 1).join('0');
    }
    return s.join(dec);
  }
  
  // Area Chart Example
  var ctx = document.getElementById("myAreaChart");
  var myLineChart = new Chart(ctx, {
    type: 'line',
    data: {
      labels: labels,
      datasets: [{
        label: "Total harmful messages",
        lineTension: 0.3,
        backgroundColor: "rgba(78, 115, 223, 0.05)",
        borderColor: "red",
        pointRadius: 3,
        pointBackgroundColor: "red",
        pointBorderColor: "red",
        pointHoverRadius: 3,
        pointHoverBackgroundColor: "red",
        pointHoverBorderColor: "red",
        pointHitRadius: 10,
        pointBorderWidth: 2,
        data: attribute_totals,
      },{
        label: "Total approved messages",
        lineTension: 0.3,
        backgroundColor: "rgba(78, 115, 223, 0.05)",
        borderColor: "#1cc88a",
        pointRadius: 3,
        pointBackgroundColor: "#1cc88a",
        pointBorderColor: "#1cc88a",
        pointHoverRadius: 3,
        pointHoverBackgroundColor: "#1cc88a",
        pointHoverBorderColor: "#1cc88a",
        pointHitRadius: 10,
        pointBorderWidth: 2,
        data: totals,
      }],
    },
    options: {
      maintainAspectRatio: false,
      layout: {
        padding: {
          left: 10,
          right: 25,
          top: 0,
          bottom: 5
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
            padding: 50,
            callback: function(value, index, values) {
              return number_format(value);
            }
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
        display: true
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
        caretPadding: 0,
        callbacks: {
          label: function(tooltipItem, chart) {
            var datasetLabel = chart.datasets[tooltipItem.datasetIndex].label || '';
            return datasetLabel + ': ' + number_format(tooltipItem.yLabel);
          }
        }
      }
    }
  });
  document.getElementById('toggle_sentiment').addEventListener('click', () => {
    myLineChart.config.data = {
      labels: labels,
      datasets: [{
        label: "Total negative messages",
        lineTension: 0.3,
        backgroundColor: "rgba(78, 115, 223, 0.05)",
        borderColor: "#ae5bd7",
        pointRadius: 3,
        pointBackgroundColor: "#ae5bd7",
        pointBorderColor: "#ae5bd7",
        pointHoverRadius: 3,
        pointHoverBackgroundColor: "#ae5bd7",
        pointHoverBorderColor: "#ae5bd7",
        pointHitRadius: 10,
        pointBorderWidth: 2,
        data: negatives,
      },{
        label: "Total positive messages",
        lineTension: 0.3,
        backgroundColor: "rgba(78, 115, 223, 0.05)",
        borderColor: "#76de83",
        pointRadius: 3,
        pointBackgroundColor: "#76de83",
        pointBorderColor: "#76de83",
        pointHoverRadius: 3,
        pointHoverBackgroundColor: "#76de83",
        pointHoverBorderColor: "#76de83",
        pointHitRadius: 10,
        pointBorderWidth: 2,
        data: positives,
      }, {
        label: "Total neutral messages",
        lineTension: 0.3,
        backgroundColor: "rgba(78, 115, 223, 0.05)",
        borderColor: "#5f69a3",
        pointRadius: 3,
        pointBackgroundColor: "#5f69a3",
        pointBorderColor: "#5f69a3",
        pointHoverRadius: 3,
        pointHoverBackgroundColor: "#5f69a3",
        pointHoverBorderColor: "#5f69a3",
        pointHitRadius: 10,
        pointBorderWidth: 2,
        data: neutrals,
      }]
    }
    myPieChart.config.data = {
      labels: ["Negative Messages", "Positive Messages", "Neutral Messages"],
      datasets: [{
      data: sentiment_breakdown,
        backgroundColor: ['#ae5bd7', '#76de83', '#5f69a3'],
        hoverBackgroundColor: ['#ae5bd7', '#76de83', '#5f69a3'],
        hoverBorderColor: "rgba(234, 236, 244, 1)",
    }]
    }

    document.getElementById('line-title').innerHTML = "Weekly Message Sentiment"
    document.getElementById('line-desc').innerHTML = "The line graph above shows a comparison of your happy, sad, and neutral messages. \
                                                      <br> With Covid-19, social distancing, and world events, it's okay to have feelings of \
                                                      anxiety, <br> sadness, and loneliness. Make sure you are looking after your mental health!"
    document.getElementById('pie-title').innerHTML = "Daily Sentiment Breakdown"
    document.getElementById('pie-desc').innerHTML = "Hover over each slice for more detailed breakdown."

    myLineChart.update();
    myPieChart.update();

    // modal trigger
    if (negatives.reduce((a,b) => a + b, 0) >=10 ) {
      document.getElementById("modal-btn").click();
  }
  });

  document.getElementById('toggle_content').addEventListener('click', () => {
    myLineChart.config.data = {
      labels: labels,
      datasets: [{
        label: "Total harmful messages",
        lineTension: 0.3,
        backgroundColor: "rgba(78, 115, 223, 0.05)",
        borderColor: "red",
        pointRadius: 3,
        pointBackgroundColor: "red",
        pointBorderColor: "red",
        pointHoverRadius: 3,
        pointHoverBackgroundColor: "red",
        pointHoverBorderColor: "red",
        pointHitRadius: 10,
        pointBorderWidth: 2,
        data: attribute_totals,
      },{
        label: "Total approved messages",
        lineTension: 0.3,
        backgroundColor: "rgba(78, 115, 223, 0.05)",
        borderColor: "#1cc88a",
        pointRadius: 3,
        pointBackgroundColor: "#1cc88a",
        pointBorderColor: "#1cc88a",
        pointHoverRadius: 3,
        pointHoverBackgroundColor: "#1cc88a",
        pointHoverBorderColor: "#1cc88a",
        pointHitRadius: 10,
        pointBorderWidth: 2,
        data: totals,
      }]
    }
    myPieChart.config.data = {
      labels: ["Toxic", "Insult", "Sexual", "Threat", "Identity Attack"],
      datasets: [{
        data: individual_attributes,
        backgroundColor: ['#4e73df', '#1cc88a', '#36b9cc', 'red', 'pink'],
        hoverBackgroundColor: ['#2e59d9', '#17a673', '#2c9faf', 'red', 'pink'],
        hoverBorderColor: "rgba(234, 236, 244, 1)",
    }]
    }

    document.getElementById('line-title').innerHTML = "Weekly Total Approved Vs. Harmful Messages"
    document.getElementById('line-desc').innerHTML = "Track the trends of your message content and digital footprint. Look to improve yourself <br>and create a safe space for everyone! Hover over each point for more details."
    document.getElementById('pie-title').innerHTML = "Daily Breakdown of Harmful Messages"
    document.getElementById('pie-desc').innerHTML = "Each colour represents a different category of a harmful message you sent. Hover over each slice for more details."

    myLineChart.update();
    myPieChart.update();
  });

})


