require("bootstrap-table");
let $table;

// formatter function for bootstrap-table
// Wrap percentages in bootstrap4 progress bars


function int2progress(value, row, index, field) {
    let numFloat = (value * 100);
    numFloat = numFloat.toFixed(2);
    return `<div class="progress">
    <div class="progress-bar" role="progressbar" style="width: ${numFloat}%" aria-valuenow="${numFloat}"
     aria-valuemin="0" aria-valuemax="100"> ${numFloat}%</div>
    </div>`;
}

function fetchSearch(json_data) {
    return new Promise(function (resolve) {
        fetch('api/v1/related', {
            method: "POST",
            headers: {
                "Accept": "application/json",
                "Content-Type": "application/json"
            },
            body: JSON.stringify(
                json_data
            )
        })
            .then(function (result) {
                if (result.status === 201) {
                    resolve([result.json(), true]);
                } else {
                    resolve([result.json(), false]);
                }
            });

    })
}

function runSearch() {
    $table.bootstrapTable('showLoading');
    const query = $("#related_autocomplete")[0].value;
    const scope = $(".btn.active input")[0].id.split("_")[1];
    let xhttp;
    let json_data = {
        q: query,
        scope: scope,
        format_input: false
    };

    xhttp = new XMLHttpRequest();
    xhttp.onreadystatechange = function () {
        if (this.readyState === 4 && this.status === 201) {
            var response_msg = JSON.parse(this.responseText);
            $table.bootstrapTable('hideLoading');
            $table.show();
            $table.bootstrapTable('load', response_msg.items);
        } else if (this.readyState === 4 && this.status === 404) {
            $table.bootstrapTable('removeAll');
            $table.bootstrapTable('hideLoading');
            $table.show();
            $table.bootstrapTable('load', {});
        }
    };
    xhttp.open("POST", '/api/v1/related', true);
    xhttp.setRequestHeader("Content-type", "application/json");
    var data = JSON.stringify(json_data);
    xhttp.send(data);
}

$(function () {

    // make enter key submit
    $(window).keydown(function (event) {
        if (event.keyCode == 13) {
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
        onPostBody: function (data) {
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
                formatter: function (value) {
                    return int2progress(value);
                }
            }
        ]
    });
});
