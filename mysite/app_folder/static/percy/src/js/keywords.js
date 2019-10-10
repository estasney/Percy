import typeahead from "typeahead.js";
import bloodhound from "bloodhound-js";

$(document).ready(function () {

    let el, output_el, graph_visible;

    // Select all range inputs, watch for change
    $("input[type='range']").change(function () {

        // Cache this for efficiency
        el = $(this);
        output_el = $(".slider-output");
        output_el.text(el.val());

        if (graph_visible === true) {
            clearGraph();
            startSearch(false, true);
        }

    });


    let data_url = "/kw_data";


    let r_base = 6;
    $('#search').on('click', startSearch);
    $('#reset').on('click', restart);
    $('#reset').on('click', enableGo);
    $('#reset').on('click', clearGraph);

    function windowSize() {
        const ws = document.getElementById('window-size');
        return ws.value;
    }

    function disableGo() {
        $('#search').addClass('disabled');
        $('#reset').removeClass('disabled');
    }

    function enableGo() {
        $('#search').removeClass('disabled');
        $('#reset').addClass('disabled');
    }

    function clearGraph() {
        graph_visible = false;
        graph = {
            "nodes": {},
            "links": {}
        };
    }

    const width = window.outerWidth;
    const height = window.outerHeight;
    let graph = {
        "nodes": {},
        "links": {}
    };


    let force = d3.layout.force().size([width, height])
        .linkDistance(function (d) {
            const source_w = d.source_n_links * 30;
            const target_w = d.target_n_links * 30;
            return Math.max(source_w, target_w);
        })
        .charge(function (d) {
            return (d.node_n_links * -300);
        })
        .gravity(0.15);
    let svg = d3.select('body').append('svg')
        .attr('width', width)
        .attr('height', height);

    function startSearch(show_modal, is_update) {
        if (show_modal === undefined) {
            show_modal = true;
        }
        if (is_update === undefined) {
            is_update = false;
        }
        let search_term;
        let active_pill = $(".nav-link.active")[0].id;
        switch (active_pill) {
            case 'v-pills-paste-tab':
                search_term = $("#search-term-paste").prop('value');
                break;
            case 'v-pills-cisco-tab':
                search_term = $("#search-term-req").prop('value');
                break;
            default:
                search_term = "";
        }
        let window_size = windowSize();
        getData(search_term, active_pill, window_size, show_modal, is_update);
        disableGo();
    }

    function appendSearch(clicked_term) {
        var limit_to = $('#limit_to').prop('value');
        getData(clicked_term, limit_to, true);
    }

    function getData(term, data_type, limit, show_modal, is_update) {
        if (show_modal === true) {
            $.LoadingOverlay("show");
        }

        $.ajax({
            type: 'POST',
            async: true,
            timeout: 10000,
            url: data_url,
            data: {
                "raw_text": term,
            },
            dataType: 'json',
            beforeSend: function (xhr) {
                xhr.setRequestHeader('Accept', 'application/json, text/javascript, */*; q=0.01');
                xhr.setRequestHeader('Accept-Language', 'en-US,en;q=0.8');
                xhr.setRequestHeader('X-Requested-With', 'XMLHttpRequest');
                xhr.setRequestHeader('Window-Limit', limit);
                xhr.setRequestHeader('Data-Type', data_type);
            },
            success: function (data) {
                if (show_modal === true) {
                    $.LoadingOverlay("hide");
                }

                var json_data = JSON.stringify(data);
                var search_data = JSON.parse(json_data).data;
                if (is_update === true) {
                    restart();
                }
                newLinks(search_data);
                graph_visible = true;
            }
        });
    }

    function newLinks(search_data) {
        function updateNodes(d) {
            d.source = graph.nodes[d.source] || (graph.nodes[d.source] = {
                node_text: d.source.valueOf(),
                node_color: d.source_color,
                node_n_links: d.source_n_links,
            });
            d.target = graph.nodes[d.target] || (graph.nodes[d.target.valueOf()] = {
                node_text: d.target.valueOf(),
                node_color: d.target_color,
                node_n_links: d.target_n_links
            });
        }

        for (var i = 0, len = search_data.length; i < len; i++) {
            updateNodes(search_data[i]);
        }
        try {
            graph.links = graph.links.concat(search_data);
        } catch (e) {
            graph.links = search_data;
        }
        startForce();
    }

    function restart() {
        svg.selectAll(".link").remove();

        svg.selectAll(".node").remove();

    }

    function startForce() {
        var links = graph.links;
        var nodes = graph.nodes;

        force.nodes(d3.values(nodes)).links(links)
            .on("tick", tick)
            .start();

        var link = svg.selectAll(".link")
            .data(force.links())
            .enter().append("line")
            .attr("class", "link");

        var node = svg.selectAll(".node")
            .data(force.nodes())
            .enter().append("g")
            .attr("class", "node")
            .on("mouseover", mouseover)
            .on("mouseout", mouseout)
            .on("click", click)
            .call(force.drag);

        node.append("circle")
            .attr("r", function (d) {
                return r_base * d.node_n_links;
            })
            .style("fill", function (d) {
                function componentToHex(c) {
                    var hex = c.toString(16);
                    return hex.length == 1 ? "0" + hex : hex;
                }

                function rgbToHex(nc) {
                    return "#" + componentToHex(nc[0]) + componentToHex(nc[1]) + componentToHex(nc[2]);
                }

                return rgbToHex(d.node_color);
            });


        node.append("text")
            .attr("x", 0)
            .attr("y", 10)
            .attr("dy", ".35em")
            .style("fill", "#333")
            .text(function (d) {
                return d.node_text;
            });

        function tick() {
            link.attr("x1", function (d) {
                return d.source.x;
            })
                .attr("y1", function (d) {
                    return d.source.y;
                })
                .attr("x2", function (d) {
                    return d.target.x;
                })
                .attr("y2", function (d) {
                    return d.target.y;
                });

            node.attr("transform", function (d) {
                return "translate(" + d.x + "," + d.y + ")";
            });
        }

        function mouseover() {
            d3.select(this).select("circle").transition()
                .duration(750)
                .attr("r", function (d) {
                    return r_base * d.node_n_links * 1.25;
                });

        }

        function mouseout() {
            d3.select(this).select("circle").transition()
                .duration(750)
                .attr("r", function (d) {
                    return r_base * d.node_n_links;
                });
        }

        // action to take on mouse click
        function click() {
            d3.select(this).select("text").transition()
                .duration(750)
                .attr("x", 22)
                .style("stroke-width", ".5px")
                .style("opacity", 1)
                .style("fill", "#E34A33")
                .style("font", "17.5px OpenSans");
            d3.select(this).select("circle").transition()
                .duration(750)
                .style("fill", "#049FD9")
                .attr("r", function (d) {
                    return d.node_n_links * 1.25;
                });

        }

    }
});
