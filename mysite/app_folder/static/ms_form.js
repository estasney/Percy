

// Adapted from https://codepen.io/atakan/pen/gqbIz
$(document).ready(function() {
  var $upload_form = $("#msform_spreadsheet");
  var $paste_form = $("#msform_paste");
  var $select_upload = $("#select-upload");
  var $select_paste = $("#select-paste");
  var $select_form = $("#select");
  var validator;
  var animating;

  // ensure sliders and output are same value in case of using backbutton
  $("[id*='female_range_']").each(function(i, e) {
    var $e = $(e);
    var output = $e.siblings('span');
    output.text($e.val() + "%");
  })

  $paste_form.on('submit', function(e) {
    var prevent_submit = false;
    current_fs = $("#submit_paste").parent();
    current_fs_elements = current_fs.find("input:not(.action-button)");
    current_fs_elements.each(function(i, e){
      if(validator.element(e) == false){
        prevent_submit = true;
      }
    });

    if(prevent_submit == false) {
      current_fs.find(".load-hide").hide();
      $("#loading_icon_paste").show();
      return true;
    } else {
      return false;
    }

  });

  $upload_form.on('submit', function(e) {
    var prevent_submit = false;
    current_fs = $("#submit_upload").parent();
    current_fs_elements = current_fs.find("input:not(.action-button)");
    current_fs_elements.each(function(i, e){
      if(validator.element(e) == false){
        prevent_submit = true;
      }
    });

    if(prevent_submit == false) {
      current_fs.find(".load-hide").hide();
      $("#loading_icon_spreadsheet").show();
      return true;
    } else{
      return false;
    }

  });

  $.validator.addMethod("minlength_list", function(value, element, params) {
    if (this.optional(element) == true) {
      return true;
    } else {
      return value.length >= params;
    }
  }, $.validator.format("Please enter at least {0} names"));



  // prevent enter key from submitting
  $(window).keydown(function(event) {
    if (event.keyCode == 13) {
      event.preventDefault();
      return false;
    }
  });

  // listen for user to choose form

  function deactivateForm(e) {
    e.attr("data-selected", false);
    e.find(".next").off();
    e.find(".previous:not([name='cancel'])").off();
    e.find("[name='cancel']").off();
    e.find("[id*='female_range']").off();
    e.hide(800);
    $select_form.show(800);

  }

  function activateForm(e, o) {
    e.attr("data-selected", true);
    o.attr("data-selected", false);
    o.hide();
    $select_form.hide(800);
    e.show(800);
    var next_btns = e.find(".next");
    var prev_btns = e.find(".previous:not([name='cancel'])");
    var cancel_btn = e.find("[name='cancel']");
    cancel_btn.on('click', function() {
      deactivateForm(e);
    });

    var slider = e.find("[id*='female_range']");
    prev_btns.on('click', function() {
      if (animating) {
        return false;
      }
      animating = true;

      current_fs = $(this).parent();
      previous_fs = $(this).parent().prev();

      //de-activate current step on progressbar
      e.find("[attribute*='progressbar']")
        .eq($("fieldset").index(current_fs))
        .removeClass("active");


      //show the previous fieldset
      previous_fs.show();
      //hide the current fieldset with style
      current_fs.animate({
        opacity: 0
      }, {
        step: function(now, mx) {
          //as the opacity of current_fs reduces to 0 - stored in "now"
          //1. scale previous_fs from 80% to 100%
          scale = 0.8 + (1 - now) * 0.2;
          //2. take current_fs to the right(50%) - from 0%
          left = ((1 - now) * 50) + "%";
          //3. increase opacity of previous_fs to 1 as it moves in
          opacity = 1 - now;
          current_fs.css({
            'left': left
          });
          previous_fs.css({
            'transform': 'scale(' + scale + ')',
            'opacity': opacity
          });
        },
        duration: 800,
        complete: function() {
          current_fs.hide();
          animating = false;
        },
        //this comes from the custom easing plugin
        easing: 'swing'
      });
    });
    next_btns.on('click', function() {
      if (animating == true) {
        return false;
      }
      var allow_next = true;
      current_fs = $(this).parent();
      next_fs = $(this).parent().next();
      current_fs_elements = current_fs.find("input:not(.action-button),textarea");
      current_fs_elements.each(function(i, e) {
        if (validator.element(e) == false) {
          console.log(e);
          allow_next = false;
        }
      });

      if (allow_next == false) {
        return false;
      }

      e.find("[attribute*='progressbar']")
        .eq($("fieldset").index(next_fs))
        .addClass("active");

      next_fs.show();

      current_fs.animate({
        opacity: 0
      }, {
        step: function(now, mx) {
          //as the opacity of current_fs reduces to 0 - stored in "now"
          //1. scale current_fs down to 80%
          scale = 1 - (1 - now) * 0.2;
          //2. bring next_fs from the right(50%)
          left = (now * 50) + "%";
          //3. increase opacity of next_fs to 1 as it moves in
          opacity = 1 - now;
          current_fs.css({
            'transform': 'scale(' + scale + ')',
            'position': 'absolute'
          });
          next_fs.css({
            'left': left,
            'opacity': opacity
          });
        },
        duration: 800,
        complete: function() {
          current_fs.hide();
          animating = false;
        },
        //this comes from the custom easing plugin
        easing: 'swing'
      });
    });
    slider.change(function() {
      var el = $(this);
      output_el = $(e.find(".slider-output-light"));
      output_el.text(el.val() + "%");

    });
  }

  $select_upload.on('click', function() {
    activateForm($upload_form, $paste_form);
    validator = $upload_form.validate({
      rules: {
        file: {
          required: true
        },
        header_name: {
          required: true
        },
        female_range: {
          required: true
        },
        beta_interval: {
          required: true,
          range: [0.01, 0.99],
          step: 0.01
        },
        sample_maximum_name_certainty: {
          required: true,
          range: [0.5, 1],
          step: 0.001
        },
        n_trials: {
          required: true,
          range: [2, 1000]
        },
        random_seed: {
          required: true,
          digits: true
        }
      }
    });
  });
  $select_paste.on('click', function() {
    activateForm($paste_form, $upload_form);
    validator = $paste_form.validate({
      rules: {
        paste_names: {
          required: true,
          normalizer: function(value) {
            // split comma by newlines or comma
            var csplit = value.split(",").length;
            var nsplit = value.split("\n").length;
            if (csplit > nsplit) {
              return value.split(",");
            } else {
              return value.split("\n");
            }
          },
          minlength_list: 2
        },
        header_name: {
          required: true
        },
        female_range: {
          required: true
        },
        beta_interval: {
          required: true,
          range: [0.01, 0.99],
          step: 0.01
        },
        sample_maximum_name_certainty: {
          required: true,
          range: [0.5, 1],
          step: 0.001
        },
        n_trials: {
          required: true,
          range: [2, 1000]
        },
        random_seed: {
          required: true,
          digits: true
        }
      }
    });
  });
});
