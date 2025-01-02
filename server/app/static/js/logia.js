function getNumberRandom(n = 10) {
  value = Math.pow(10, n) - 1
  return Math.floor(Math.random() * value) + 1;
}
//================================================================================
// valida mail
//================================================================================
const email_input = document.getElementById('username');
if (email_input) {
  email_input.addEventListener('input', emailEval);
}

async function emailEval( rutCompleto ) {
  var tmp = rutCompleto.split('@');
  if (tmp.length == 2) {  
    var dominio = tmp[1];
    var values = dominio.split('.');
    if (values.length == 2) {
        if (values[0].length > 0 && values[1].length > 0) return true;
    }
  }
  return false;
}

$("#btnIngresar").submit( function(evt) {
  let mail = $("#username").val();
  if (mail) {
      if (emailEval(mail)) {
          return;
      } else {
          evt.preventDefault();
          alert("Formato de mail incorrecto");
      }
  }
});

//================================================================================
// evalua el token del recapcha
//================================================================================
async function captchaValueToken( e )  {
  console.info('############ Token: ', e)
  var dataTx = {
    response: e
  }
  console.info('DataTx: ', JSON.stringify(dataTx))
  // Alerta 
  document.getElementById("btnIngresar").disabled = true

  response = await fetch('https://logia.buenaventuracadiz.cl/bcp/hcaptcha', {
    method: 'POST', 
    mode: 'cors', 
    headers: {
      'Content-Type': 'application/json',
      'Access-Control-Allow-Origin': 'logia.buenaventuracadiz.cl',
    },
    body: JSON.stringify(dataTx) 
  }).catch(error => {
    console.error('Error detectado:', error)
  });

  if (response.ok && response.status == 200) {        
    dataRx = await response.json()
    console.info('DataRx: ', JSON.stringify(dataRx))
    document.getElementById("btnIngresar").disabled = !dataRx.success
  } else {
    console.warn('Response: ', response)
  }


  return response
}
