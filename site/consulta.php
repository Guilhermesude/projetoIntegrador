<?php 
  session_start();

  if(empty($_SESSION['Cod_Usuario'])){
      
      $_SESSION['paginaAtual'] = 'consulta.php';
      header('location:login.php');
  }
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    
        
</head>
<body>
    <img src="imagens/pedreiro.png" alt="some text" width=1000 height=500>
    <h1 style="margin-left: 45px; color:black"> 
      Página em construção!
    </h1>
    
</body>
</html>
