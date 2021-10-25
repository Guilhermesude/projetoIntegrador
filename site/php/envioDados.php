<?php 

    /*Inclue o arquivo credenciaisBanco.php para utilizar as suas variaveis para se conectar ao banco de dados */
    include_once 'credenciaisBanco.php';

    extract($_GET);
    extract($_POST);

    print_r($_GET);
    print_r($_POST);

    $dadosTitular = "INSERT INTO `titular` (
                        `nome`, `endereco`, `complemeto`, `bairro`, `cep`, `cidade`, `estado`, `naturalidade`, 
                        `data_nasc`, `estado_civil`, `sexo`, `escolaridade`, `profissao`, `renda`, `telefone`, 
                        `celular`, `telefone_rec`, `e-mail`, `facebook`, `nis`, `rg`, `cpf`, `titulo`, `zona`, 
                        `secao`, `moradia`) 
                    VALUES (
                        '".$nome."', '".$endereco."', '".$complemento."', '".$bairro."', '".$cep."', '".$cidade."', '".$estado."',
                        '".$naturalidade."', '".$dataNascimento."', '".$estadoCivil."', '".$sexo."', '".$escolaridade."', '".$profissao."', 
                        '".$renda."', '".$telefone."', '".$celular."', '".$telRecado."', '".$e_mail."', '".$facebook."', '".$nis."', '".$rg."', 
                        '".$cpf."', '".$titulo."', '".$zonaEleitoral."', '".$sessaoEleitoral."', '".$moradia."')";

    $db->query($dadosTitular);

    echo $dadosTitular;
                    
    header('Location:index.html');

?>