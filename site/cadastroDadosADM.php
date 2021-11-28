<?php 
    include_once 'credenciaisBanco.php';
    print_r($_POST);

    echo '<br><br><br>',count($_POST),'<br><br><br>';
    extract($_POST); 

    $dadosADM = "INSERT INTO `cadastro_ong`.`usuarios` (`Nome_de_Usuario`, `Email`, `Senha`, `Tipo_de_Usuario`) 
                     VALUES ('".$nome."', '".$email."', sha2('".$senha."',256), '".$tipoUsuario."')";
                         
                        
                        
    $db->query($dadosADM);

    header('location:index.html');
    





?>
