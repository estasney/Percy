// formatter function for bootstrap-table
// Wrap percentages in bootstrap4 progress bars

var $table;


function int2progress(value, row, index, field){
  var num = (value * 100).toFixed(2);
  var html = render({n:num});
  return html;
}

function render(data, options) {
  return (function($) {
    var get = $.get, set = $.set, push = $.push, pop = $.pop, write = $.write, filter = $.filter, each = $.each, block = $.block;
    write("<div class=\"progress\">\n  <div class=\"progress-bar\" role=\"progressbar\" style=\"width: ");
    filter(get("n"));
    write("%;\" aria-valuenow=\"");
    filter(get("n"));
    write("\" aria-valuemin=\"0\" aria-valuemax=\"100\">");
    filter(get("n"));
    write("%</div>\n</div>");
    return $.render();
  })(runtime(data, options));
}

function runSearch() {
  $table.bootstrapTable('showLoading');
  var query = $("#related_autocomplete")[0].value;
  var scope = $(".btn.active input")[0].id.split("_")[1];
  var xhttp;
  var json_data = {
    q: query,
    scope: scope
    };

  xhttp = new XMLHttpRequest();
  xhttp.onreadystatechange = function() {
    if (this.readyState === 4 && this.status === 201) {
      var response_msg = JSON.parse(this.responseText);
      $table.bootstrapTable('hideLoading');
      $table.show();
      $table.bootstrapTable('load', response_msg.items);
    }
  };
  xhttp.open("POST", '/api/v1/related', true);
  xhttp.setRequestHeader("Content-type", "application/json");
  var data = JSON.stringify(json_data);
  xhttp.send(data);
}

$(function() {

  // make enter key submit
  $(window).keydown(function(event){
    if(event.keyCode == 13) {
      runSearch();
    }
  });



  var search_btn = $("#search-btn");
  search_btn.on('click', runSearch);
  $table = $("#results-table");
  $table.bootstrapTable({
    pagination: true,
    sortable: true,
    showRefresh: false,
    sortName: 'score',
    sortOrder: 'desc',
    uniqueId: 'word',
    striped: true,
    search: false,
    onPostBody: function(data) {
      // data.forEach(function(d, index) {
      //   updateToolTip(d);
      // });
      // setupListeners();
      console.log(data);
    },
    columns: [
      {
        field: 'word',
        title: 'Word',
        sortable: true,
      }, {
        field: 'score',
        title: 'Similarity',
        sortable: true,
        formatter: function(value) {
          return int2progress(value);
        }
      }
    ]
  });
});
