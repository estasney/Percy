
// Adapted from https://codepen.io/atakan/pen/gqbIz
$(document).ready(function() {

  // prevent enter key from submitting
  $(window).keydown(function(event){
    if(event.keyCode == 13) {
      event.preventDefault();
      return false;
    }
  });

  var current_fs, next_fs, previous_fs; //fieldsets
  var left, opacity, scale; //fieldset properties which we will animate
  var animating; //flag to prevent quick multi-click glitches
  var form = $("#msform");

  form.on('submit', function() {
    var btns = $(".load-hide");
    btns.each(function(i, e) {
      $(e).hide(500);
    });
    $("#loading-icon").show();

  })



  // field inputs

  var validator = form.validate({
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
      sample_min_size: {
        required: true
      },
      sample_min_size_uniform: {
        required: true
      }
    }
  });

  $(".next").click(function(){
    var allow_next = true;
  	if(animating) return false;

    current_fs = $(this).parent();
  	next_fs = $(this).parent().next();

    // validate the current_fs

    current_fs_elements = current_fs.find("input:not(.action-button)");
    current_fs_elements.each(function(i, e){
      if (validator.element(e) == false) {
        allow_next = false;
      }
    })

    if (allow_next == false) {
      return false;
    }


  	animating = true;


    //activate next step on progressbar using the index of next_fs
  	$("#progressbar li").eq($("fieldset").index(next_fs)).addClass("active");
    next_fs.show();

    //show the next fieldset
    current_fs.animate({opacity: 0}, {
  		step: function(now, mx) {
  			//as the opacity of current_fs reduces to 0 - stored in "now"
  			//1. scale current_fs down to 80%
  			scale = 1 - (1 - now) * 0.2;
  			//2. bring next_fs from the right(50%)
  			left = (now * 50)+"%";
  			//3. increase opacity of next_fs to 1 as it moves in
  			opacity = 1 - now;
  			current_fs.css({
          'transform': 'scale('+scale+')',
          'position': 'absolute'
        });
  			next_fs.css({'left': left, 'opacity': opacity});
  		},
  		duration: 800,
  		complete: function(){
  			current_fs.hide();
  			animating = false;
  		},
  		//this comes from the custom easing plugin
  		easing: 'swing'
  	});
  });

  $(".previous").click(function(){
  	if(animating) return false;
  	animating = true;

  	current_fs = $(this).parent();
  	previous_fs = $(this).parent().prev();

  	//de-activate current step on progressbar
  	$("#progressbar li").eq($("fieldset").index(current_fs)).removeClass("active");

  	//show the previous fieldset
  	previous_fs.show();
  	//hide the current fieldset with style
  	current_fs.animate({opacity: 0}, {
  		step: function(now, mx) {
  			//as the opacity of current_fs reduces to 0 - stored in "now"
  			//1. scale previous_fs from 80% to 100%
  			scale = 0.8 + (1 - now) * 0.2;
  			//2. take current_fs to the right(50%) - from 0%
  			left = ((1-now) * 50)+"%";
  			//3. increase opacity of previous_fs to 1 as it moves in
  			opacity = 1 - now;
  			current_fs.css({'left': left});
  			previous_fs.css({'transform': 'scale('+scale+')', 'opacity': opacity});
  		},
  		duration: 800,
  		complete: function(){
  			current_fs.hide();
  			animating = false;
  		},
  		//this comes from the custom easing plugin
  		easing: 'swing'
  	});
  });

  $("#female_range").change(function() {

     // Cache this for efficiency
     el = $(this);
     output_el = $(".slider-output-light");
     output_el.text(el.val()+"%");
  });

});
