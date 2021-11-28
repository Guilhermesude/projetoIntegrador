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
    <title>Document</title>
    <h1>Isso aqui funcionou!!!!!!</h1>
</head>
<body>
    
</body>
</html>