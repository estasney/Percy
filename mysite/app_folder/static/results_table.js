// formatter function for bootstrap-table
// Wrap percentages in bootstrap4 progress bars

function int2progress(value, row, index, field){
  var num = (value * 100).toFixed(2);
  var html = render({n:num});
  return html
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
  })(runtime(data, options))
}
