<?php 
    session_start();
    echo $_SESSION['Cod_Usuario'];
    if(!empty($_SESSION['Cod_Usuario'])){
        
        header('location:cadastro.php');
        echo 'pagina de seleção de ações para ADM';
    }else{
        session_unset();
        session_destroy();
    }
?>

<form name="login" id="login" action="envioDados.php">

    <label from="email">Email</label>
    <input name="email" type="email" id="email">
    
    <br><br>

    <label from="senha">Senha</label>
    <input name="senha" type="password" id="senha">
    
    <br><br>
    <button type="button" id="dadosLogin" style="color: green;" >Entrar</button>

</form>


<script type="text/javascript" src="js/funcionalidadeBotoes.js" defer></script>