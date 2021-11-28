<?php 
    include_once 'credenciaisBanco.php';
    print_r($_POST);

    echo '<br><br><br>',count($_POST),'<br><br><br>';
    extract($_POST); 

/** Inserção de novos dados de associados -------------------------------------------------------------------------------------------------------- */
  /*
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
  */

    $dadosTitular = "INSERT INTO `titular` (
                          `nome`, `endereco`, `complemeto`, `bairro`, `cep`, `cidade`, `estado`, `naturalidade`, 
                          `data_nasc`, `estado_civil`, `sexo`, `escolaridade`, `profissao`, `renda`, `telefone`, 
                          `celular`, `telefone_rec`, `e-mail`, `facebook`, `nis`, `rg`, `cpf`, `titulo`, `zona`, 
                          `secao`, `moradia`, `ativo`)
                    VALUES(
                        '".$nome."', '".$endereco."', '".$complemento."', '".$bairro."', '".$cep."', '".$cidade."', '".$estado."',
                        '".$naturalidade."', '".$dataNascimento."', '".$estadoCivil."', '".$sexo."', '".$escolaridade."', '".$profissao."',
                        '".$renda."', '".$telefone."', '".$celular."', '".$telRecado."', '".$e_mail."', '".$facebook."', '".$nis."', 
                        '".$rg."', '".$cpf."', '".$titulo."', '".$zonaEleitoral."', '".$sessaoEleitoral."', '".$moradia."', 'Sim')";
                         
                        
                            
    
    $db->query($dadosTitular);

     echo $dadosTitular;
  





?>
