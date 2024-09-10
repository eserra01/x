$(document).ready(function(){

  // Solo números en campo de teléfono
  $("input[name='phone_toll']").keydown(function(event) {
    if(isNaN(event.key) && event.key !== 'Backspace') {
      event.preventDefault();
    }
  });

  $("input[name='phone']").keydown(function(event) {
    if(isNaN(event.key) && event.key !== 'Backspace') {
      event.preventDefault();
    }
  });
});