var $ = require("jquery");
require("jquery-ui");

window.addEventListener("load", function () {

    let substringMatcher = function (strs) {
        return function findMatches(q, cb) {
            // an array that will be populated with substring matches
            let matches = [];

            // regex used to determine if a string contains the substring `q`
            let substringRegex = new RegExp(q, 'i');

            // iterate through the pool of strings and for any string that
            // contains the substring `q`, add it to the `matches` array
            $.each(strs, function (i, str) {
                if (substringRegex.test(str)) {
                    matches.push(str);
                }
            });
            cb(matches);
        };
    };

    // set words to autocomplete
    $.ajax({
        url: '/autocomplete'
    }).done(function (data) {
        $('.typeahead').typeahead({
            hint: true,
            highlight: true,
            minLength: 2,
            classNames: {
                menu: 'pt-menu',
                suggestion: 'pt-suggestion',
                open: 'pt-open',
                highlight: 'pt-highlight',
                cursor: 'pt-cursor'
            }
        }, {
            'name': 'words',
            source: substringMatcher(data)
        });
    });


    function radioClicked(e) {
        let $e = $(e.target);
        let radioId = $e.children().first().prop('id');

        // clear inputs
        $(".twitter-typeahead input").each(function (i, e) {
            $(e).val("");
        });

        if (radioId === 'scope_skills') {
            $(".typeahead").typeahead("destroy");
            $.ajax({
                url: '/autocomplete/skills'
            }).done(function (data) {
                $('.typeahead').typeahead({
                    hint: true,
                    highlight: true,
                    minLength: 2,
                    classNames: {
                        menu: 'pt-menu',
                        suggestion: 'pt-suggestion',
                        open: 'pt-open',
                        highlight: 'pt-highlight',
                        cursor: 'pt-cursor'
                    }
                }, {
                    'name': 'skills',
                    source: substringMatcher(data)
                });
            });
        } else {
            $(".typeahead").typeahead("destroy");
            $.ajax({
                url: '/autocomplete'
            }).done(function (data) {
                $('.typeahead').typeahead({
                    hint: true,
                    highlight: true,
                    minLength: 2,
                    classNames: {
                        menu: 'pt-menu',
                        suggestion: 'pt-suggestion',
                        open: 'pt-open',
                        highlight: 'pt-highlight',
                        cursor: 'pt-cursor'
                    }
                }, {
                    'name': 'words',
                    source: substringMatcher(data)
                });
            });
        }
    }

    $(".btn-group.btn-group-toggle > label").on('click', radioClicked);

});
