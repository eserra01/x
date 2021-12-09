$( document ).ready(function() {

  $("#birthdate").focus(function() {}).blur(function() {
    var today = new Date();
    var dd = String(today.getDate()).padStart(2, '0');
    var mm = String(today.getMonth() + 1).padStart(2, '0'); //January is 0!
    var yyyy = today.getFullYear();

    today = yyyy + '-' + mm + '-' + dd;
    if($(this).val().split("-")[0] < 100){
      var qwe  = "19"+$(this).val().split("-")[0][2]+$(this).val().split("-")[0][3];
      $(this).val( qwe+"-"+$(this).val().split("-")[1]+"-"+$(this).val().split("-")[2] );
    } else if ($(this).val().split("-")[0] >= 100 & $(this).val().split("-")[0] <1910 | $(this).val() >= today){
      alert("El formato de fecha no es correcto, favor de verificarlo");
      $(this).val(null);
      $(this.focus());
    }
    if ($(this).val().split("-")[0].length >4){
      alert("El campo de año contiene más de 4 digitos, favor de verificarlo");
      $(this).val(null);
    }
    });


  /* Método de formateo de string */
  String.prototype.format = function() {
    var str = this;
    for (var i = 0; i < arguments.length; i++) {
      var reg = new RegExp("\\{" + i + "\\}", "gm");
      str = str.replace(reg, arguments[i]);
    }
    return str;
  }

  /* LLENADO DE INFORMACIÓN DE LA COMPAÑIA */
  $("#act_button").click(function() {
    var value = $("#company option:selected");
    if(value.val() == '0'){
      alert( "Favor de Elegir una ciudad" );
    } else {
      /* LIMPIAR TODOS LOS CAMPOS */
      $("#agent_id").prop('required',true);
      $("#lot_id").val('').prop('required',true);
      $("#partner_name").val('').prop('required',true);
      $("#partner_fname").val('').prop('required',true);
      $("#partner_mname").val('').prop('required',true);
      $("#birthdate").val('').prop('required',true);
      $("#phone").val('').prop('required',true);
      $("#municipality_id").find("option").remove().end().prop('required',true);
      $("#neighborhood_id").find("option").remove().end().prop('required',true);
      $("#payment_scheme_id").find("option").remove().end().prop('required',true);
      $("#street_name").val('').prop('required',true);
      $("#street_number").val('').prop('required',true);
      $("#between_streets").val('');
      $("#zip_code").val('').prop('required',true);
      $("#comment").val('');
      $("#employee_id").text('');
      $("#product_id").text('');

      var title = "{0}".format(value.text());
      $("#modal-title").text(title);
      $("#activation-form").modal("show");
      $.post("/main/company", {'company_id' : value.val()}, function(data) {
        if(data.result != null) {
          for(var i = 0;i < data.result.municipality_id.length; i++) {
            $("#municipality_id").append("<option value={0}>{1}</option>".format(data.result.municipality_id[i].id, data.result.municipality_id[i].name));
          }
          for(var i = 0; i< data.result.neighborhood_id.length; i++) {
            $("#neighborhood_id").append("<option value={0}>{1}</option>".format(data.result.neighborhood_id[i].id, data.result.neighborhood_id[i].name));
          }
        }
      });
    }
  });

  $("#lot_id").change(function () {
    $("#schemes").empty();
    var company_id = $("#company option:selected").val();
    var lot_id = $( this ).val();
    $("#activation_code").text("");
    $.post('/main/check/serie', {'company_id' : company_id, 'lot_id' : lot_id}, function(data) {
      if (data.result != null) {
        if (data.result.employee) {
          $("#employee_id").text(data.result.employee);
        } else {

        }
        if (data.result.product) {
          $("#product_id").text(data.result.product);
        }
        if (data.result.schemes) {
          var schemes = '';
          for (var i = 0; i< data.result.schemes.length; i++){
            schemes = schemes + '<option value="{0}">{1}</option>'.format(data.result.schemes[i].id, data.result.schemes[i].name);
          }
          $("#schemes").append('<label for="payment_scheme_id">Esquema de Pago</label><select id="payment_scheme_id" name="payment_scheme_id" class="form-control">{0}</select>'.format(schemes))
        }
        if (data.result.message) {
          $("#employee_id").text('');
          $("#product_id").text('');
          $("#lot_id").val('');
          alert(data.result.message);
        }
      }
    });
  });

  $("#activation_form").submit(function (){
    $("#submit").addClass("disabled");
    var company_id = $("#company option:selected").val();
    var args = "company_id={0}&".format(company_id);
    var args = args + $("#activation_form").serialize();
    $.ajax({
      type: "POST",
      data: args,
      url: "/main/activation/set",
      success: function(data)
        {
          if(data.result.activation_code != null) {
            if(confirm('Código de activación : {0}\n¿Deseas seguir activando?'.format(data.result.activation_code))){
              $("#activation_code").text("Código: {0}".format(data.result.activation_code));
              $("#lot_id").val('');
              $("#partner_name").val('');
              $("#partner_fname").val('');
              $("#partner_mname").val('');
              $("#birthdate").val('');
              $("#phone").val('');
              $("#municipality_id").val($("#target option:first").val());
              $("#neighborhood_id").val($("#target option:first").val());
              $("#payment_scheme_id").val($("#target option:first").val());
              $("#street_name").val('');
              $("#street_number").val('');
              $("#between_streets").val('');
              $("#zip_code").val('');             
              $("#comment").val('');
              $("#employee_id").text('');
              $("#product_id").text('');
            } else {
              $("#activation_code").text("");
              $("#activation-form").modal("hide");
            }
          }
          if (data.result.message) {
            alert(data.result.message);
          }
          return false;
        }
    });
    return false;
  });
});
