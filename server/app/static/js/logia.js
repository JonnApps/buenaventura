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
  console.info('############ emailEval')
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

async function sendwork() {
  console.info('############ sendwork: /bcp/work/add ')
  const md5 = document.getElementById('md5doc').value;
  if (md5.length == 0){
    alert("Seleccione un archivo primero");
    return;
  }
  if (document.getElementById('title').value.length == '0') {
    alert("Debe ingresar un titulo");
    return;
  }
  if (document.getElementById('author').value.length == '0') {
    alert("Debe ingresar un autor del trabajo");
    return;
  }

  switch ( document.getElementById('type').value ) {
    case 'PROGRAM':
    case 'WORK':
    case 'ADDITIONAL':
      break;
    default: 
      alert("Debe seleccionar un tipo de documento");
      return;
  }

}

//convierte en base64 y sube
async function uploadFile() {
  console.info('############ uploadFile!!! ')

  const fileInput = document.getElementById('namefile');
  const statusDiv = document.getElementById('status_file');
  const md5 = document.getElementById('md5doc');
  const grade = document.getElementById('grade');
  
  let folder = 'docs';
  switch (grade.value) {
      case '1' : folder = folder + '/primero'; break;
      case '2' : folder = folder + '/segundo'; break;
      case '3' : folder = folder + '/tercero'; break;
      default: {
        statusDiv.className = 'error';
        statusDiv.innerHTML = `<strong><span style="color: red;">Error:</span></strong> Debe seleccionar un grado.`;
        return;
      };
  }

  const file = fileInput.files[0];

  if (!file) {
      statusDiv.className = 'error';
      statusDiv.textContent = 'Por favor, selecciona un archivo primero.';
      return;
  }

  statusDiv.className = '';
  statusDiv.textContent = 'Enviando al servidor...';

  const reader = new FileReader();

  reader.onload = async function(event) {
      const base64String = event.target.result;
      // Extraer solo la parte Base64 (eliminar "data:image/png;base64," si existe)
      const type = base64String.split(',')[0]; 
      const base64Only = base64String.split(',')[1]; 
      
      statusDiv.className = '';
      statusDiv.textContent = 'Enviando al servidor...';

      try {
          const response = await fetch('/bcp/work/upload', {
              method: 'POST',
              mode: 'cors', 
              headers: {
                  'Content-Type': 'application/json',
                  'Access-Control-Allow-Origin': 'logia.buenaventuracadiz.cl',
              },
              body: JSON.stringify({
                  file_name: file.name,
                  file_data: base64Only,
                  file_type: type,
                  file_folder: folder,
              }),
          });

          const result = await response.json();
          console.log('Resultado:',result);
          if (response.ok) {
              statusDiv.className = 'success';
              statusDiv.innerHTML = `<strong>¡Éxito!</strong> ${result.message}`;
              md5.value = result.md5;
              // grade.disabled = true;
          } else {
              statusDiv.className = 'error';
              statusDiv.innerHTML = `<strong><span style="color: red;">Error:</span></strong> ${result.error || 'Algo salió mal'}`;
              md5.value = "";
          }
      } catch (error) {
          statusDiv.className = 'error';
          statusDiv.textContent = `Error de red o servidor: ${error.message}`;
          console.error('Error:', error);
      }
  };

  reader.onerror = function(error) {
      statusDiv.className = 'error';
      statusDiv.textContent = `Error al leer el archivo: ${error}`;
      console.error('FileReader error:', error);
  };

  reader.readAsDataURL(file); // Lee el archivo como una URL de datos (Base64)
}

//================================================================================
// evalua el token del recapcha
//================================================================================
async function captchaValueToken( e )  {
  var dataTx = {
    response: e
  }
  // Alerta 
  document.getElementById("btnIngresar").disabled = true
  response = await fetch('/bcp/hcaptcha', {
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
