function getNumberRandom(n = 10) {
  value = Math.pow(10, n) - 1
  return Math.floor(Math.random() * value) + 1;
}
//================================================================================
// genera un UUID
//================================================================================
function generateUUID() {
  var d = new Date().getTime();
  var d2 = ((typeof performance !== 'undefined') && performance.now && (performance.now() * 1000)) || 0;
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function (c) {
    var r = Math.random() * 16;
    if (d > 0) {
      r = (d + r) % 16 | 0;
      d = Math.floor(d / 16);
    } else {
      r = (d2 + r) % 16 | 0;
      d2 = Math.floor(d2 / 16);
    }
    return (c === 'x' ? r : (r & 0x3 | 0x8)).toString(16);
  });
}

//================================================================================
// genera la fecha actual en formato solicitado
//================================================================================
function getDateContract(mode = 'd-m-a') {
  d = new Date()
  year = String(d.getUTCFullYear())
  month = String(d.getUTCMonth() + 1)
  month = d.getUTCMonth() < 10 ? ('0' + month) : month
  day = String(d.getDate())
  day = d.getDate() < 10 ? ('0' + day) : day
  ret = year + month + day
  if (mode === 'd-m-a')
    ret = day + '-' + month + '-' + year
  if (mode === 'a-m-d')
    ret = year + '-' + month + '-' + day
  return ret
}

//================================================================================
// genera un UUID
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
