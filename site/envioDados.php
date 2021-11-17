<?php 

  /*Inclue o arquivo credenciaisBanco.php para utilizar as suas variaveis para se conectar ao banco de dados */
  include_once 'credenciaisBanco.php';

  extract($_POST);
  extract($_GET);
  //print_r($dadosForm);
  //print_r($_POST);
  //var_dump(json_decode($dadosForm));



  /** Verificação de email e senha para login*/
  try{   
    
    $SQL = "SELECT Cod_Usuario,Nome_de_Usuario,Tipo_de_Usuario FROM usuarios WHERE Email='$email' and Senha=sha2('$senha',(256))";
    $query = $db->prepare($SQL);
		$query->execute();
		$result = $query->fetchAll(PDO::FETCH_ASSOC);

  }catch(PDOException $e){
    header("location: index.html");
  }

  /** Cria variaveis de sessão e permite o carregamento da pagina de cadastro */
  if(!empty($result[0]['Cod_Usuario'])){

    $_SESSION['Usuario']     = $result[0]['Nome_de_Usuario'];
    $_SESSION['TipoUsuario'] = $result[0]['Tipo_de_Usuario'];
    $_SESSION['Cod_Usuario'] = $result[0]['Cod_Usuario'];
    
    echo 'true';

  }else{
    echo 'false';
  }
/** Inserção de novos dados de associados -------------------------------------------------------------------------------------------------------- 

  *  $dadosTitular = "INSERT INTO `titular` (
  *                      `nome`, `endereco`, `complemeto`, `bairro`, `cep`, `cidade`, `estado`, `naturalidade`, 
  *                      `data_nasc`, `estado_civil`, `sexo`, `escolaridade`, `profissao`, `renda`, `telefone`, 
  *                      `celular`, `telefone_rec`, `e-mail`, `facebook`, `nis`, `rg`, `cpf`, `titulo`, `zona`, 
  *                      `secao`, `moradia`) 
  *                  VALUES (
  *                      '".$nome."', '".$endereco."', '".$complemento."', '".$bairro."', '".$cep."', '".$cidade."', '".$estado."',
  *                      '".$naturalidade."', '".$dataNascimento."', '".$estadoCivil."', '".$sexo."', '".$escolaridade."', '".$profissao."', 
  *                      '".$renda."', '".$telefone."', '".$celular."', '".$telRecado."', '".$e_mail."', '".$facebook."', '".$nis."', '".$rg."', 
  *                      '".$cpf."', '".$titulo."', '".$zonaEleitoral."', '".$sessaoEleitoral."', '".$moradia."')";

  *  $db->query($dadosTitular);

  *---------------------------------------------------------------------------------------------------------------------------------------------- */

  //  echo $dadosTitular;
                    
    //header('Location:/site');

?>