window.addEventListener("load", function() {

  var substringMatcher = function(strs) {
    return function findMatches(q, cb) {
      var matches, substringRegex;

      // an array that will be populated with substring matches
      matches = [];

      // regex used to determine if a string contains the substring `q`
      substrRegex = new RegExp(q, 'i');

      // iterate through the pool of strings and for any string that
      // contains the substring `q`, add it to the `matches` array
      $.each(strs, function(i, str) {
        if (substrRegex.test(str)) {
          matches.push(str);
        }
      });

      cb(matches);
    };
  };

  // set words to autocomplete
  $.ajax({
    url: '/autocomplete'
  }).done(function(data) {
    $('.typeahead').typeahead({
      hint: true,
      highlight: true,
      minLength: 1,
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
    var radioId = e.target.id;
    if (radioId == 'skillsradio') {
      $(".typeahead").typeahead("destroy");
      $.ajax({
        url: '/autocomplete_skills'
      }).done(function(data) {
        $('.typeahead').typeahead({
          hint: true,
          highlight: true,
          minLength: 1,
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
      }).done(function(data) {
        $('.typeahead').typeahead({
          hint: true,
          highlight: true,
          minLength: 1,
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

  $("#skillsradio").on('click', radioClicked);
  $("#wordsradio").on('click', radioClicked);

});
