function getNumberRandom(n = 10) {
  value = Math.pow(10, n) - 1
  return Math.floor(Math.random() * value) + 1;
}
//================================================================================
// valida el rut
//================================================================================

const input_rut = document.getElementById('username');
input_rut.addEventListener('input_rut', rutEval);

async function rutEval( rutCompleto ) {
  if (!/^[0-9]+-[0-9kK]{1}$/.test(rutCompleto))
      return false;
  var tmp = rutCompleto.split('-');
  var digv = tmp[1];
  var rut = tmp[0];
  if (digv == 'K') digv = 'k';
  return (Fn.dv(rut) == digv);
}

async function dv(T) {
  var M = 0,
      S = 1;
  for (; T; T = Math.floor(T / 10))
      S = (S + T % 10 * (9 - M++ % 6)) % 11;
  return S ? S - 1 : 'k';
}

$("#login").submit( function(evt) {
  let rut = $("#username").val();
  if (rut) {
      if (rutEval(rut)) {
          return;
      } else {
          evt.preventDefault();
          alert("Formato de RUT debe ser xxxxxxxx-x sin puntos");
      }
  } else {
      console.log("validarrut:");
      if (Fn.validaRut(rutShipping)) {
          return;
      } else {
          evt.preventDefault();
          alert("Formato de RUT en dirección de envio debe ser xxxxxxxx-x sin puntos");
      }
  }
});

//================================================================================
// evalua el token del recapcha
//================================================================================
async function tokenEval( e )  {
  console.info('############ Token: ', e)
  var dataTx = {
    response: e
  }
  console.info('DataTx: ', JSON.stringify(dataTx))
  // Alerta 
  document.getElementById("btnNext").disabled = true

  response = await fetch('https://logia.buenaventuracadiz.com/page/hcaptcha', {
    method: 'POST', 
    mode: 'cors', 
    headers: {
      'Content-Type': 'application/json',
      'Access-Control-Allow-Origin': 'logia.buenaventuracadiz.com',
    },
    body: JSON.stringify(dataTx) 
  }).catch(error => {
    console.error('Error detectado:', error)
  });

  if (response.ok && response.status == 200) {        
    dataRx = await response.json()
    console.info('DataRx: ', JSON.stringify(dataRx))
    document.getElementById("btnNext").disabled = !dataRx.success
  } else {
    console.warn('Response: ', response)
  }


  return response
}
