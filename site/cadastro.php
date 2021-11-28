<?php 
  session_start();
  //print_r($_SESSION);
  if(empty($_SESSION['Cod_Usuario'])){
      
      $_SESSION['paginaAtual'] = 'cadastro.php';
      header('location:login.php');
  }
?>

<div>
  <form class="row g-3" style="margin-left: 30px;" action="cadastroAssociados.php" method="POST">
      <div class="col-md-8">
        <label for="nomeCompleto" class="form-label">Nome do titular</label>
        <input name="nome" class="form-control" type="text" id="nomeCompleto" placeholder="Nome completo" >
      </div>
      
      <div class="col-md-3">
        <label for="NumMatricula" class="form-label">Matricula</label>
        <input name="matricula" class="form-control" type="text" id="NumMatricula" placeholder="Matricula">
      </div>

      <div class="col-md-5">
        <label for="endereco" class="form-label">Endereço</label>
        <input name="endereco" class="form-control" type="text" id="endereco" placeholder="Endereço">            
      </div>

      <div class="col-md-3">
        <label for="complemento" class="form-label">Complemento</label>
        <input name="complemento" class="form-control" type="text" id="complemento" placeholder="Complemento">
      </div>

      <div class="col-md-3">
        <label for="bairro" class="form-label">Bairro</label>
        <input name="bairro" class="form-control" type="text" id="bairro" placeholder="bairro">
      </div>

      <div class="col-md-2">
        <label for="cep" class="form-label">CEP</label>
        <input name="cep" class="form-control" type="text" id="cep" placeholder="01234-569">
      </div>
      
      <div class="col-md-2">
        <label for="cidade" class="form-label">Cidade</label>
        <input name="cidade" class="form-control" type="text" id="cidade" placeholder="São paulo">
      </div>

      <div class="col-md-2">
        <label for="estado" class="form-label">Estado</label>
        <select id="estado" name="estado" class="form-select form-control">
          <option disabled value="" selected>Selecionar</option>
          <option value="AC">Acre</option>
          <option value="AL">Alagoas</option>
          <option value="AP">Amapá</option>
          <option value="AM">Amazonas</option>
          <option value="BA">Bahia</option>
          <option value="CE">Ceará</option>
          <option value="DF">Distrito Federal</option>
          <option value="ES">Espírito Santo</option>
          <option value="GO">Goiás</option>
          <option value="MA">Maranhão</option>
          <option value="MT">Mato Grosso</option>
          <option value="MS">Mato Grosso do Sul</option>
          <option value="MG">Minas Gerais</option>
          <option value="PA">Pará</option>
          <option value="PB">Paraíba</option>
          <option value="PR">Paraná</option>
          <option value="PE">Pernambuco</option>
          <option value="PI">Piauí</option>
          <option value="RJ">Rio de Janeiro</option>
          <option value="RN">Rio Grande do Norte</option>
          <option value="RS">Rio Grande do Sul</option>
          <option value="RO">Rondônia</option>
          <option value="RR">Roraima</option>
          <option value="SC">Santa Catarina</option>
          <option value="SP">São Paulo</option>
          <option value="SE">Sergipe</option>
          <option value="TO">Tocantins</option>
          <option value="EX">Estrangeiro</option>
      </select>
      </div>

      <div class="col-md-2">
        <label for="moradia" class="form-label">Moradia</label>
        <select id="moradia" name="moradia" class="form-select form-control">
          <option disabled value="" selected>Selecionar</option>
          <option value="Aluguel">Aluguel</option>
          <option value="Cedida">Cedida</option>
          <option value="Favela">Favela</option>
          <option value="Ocupacao">Ocupação</option>
          <option value="Area_livre">Área livre</option>
          <option value="Area_risco">Área de risco</option>
      </select>
      </div>


      <div class="col-md-3">
        <label for="naturalidade" class="form-label">Naturalidade</label>
        <input name="naturalidade" class="form-control" type="text" id="naturalidade" placeholder="Cidade, Estado">
      </div>

      <div class="col-md-3">
        <label for="dataNascimento" class="form-label">Data de Nascimento</label>
        <input name="dataNascimento" class="form-control" type="date" id="dataNascimento">
      </div>

      <div class="col-md-3">
        <label for="estadoCivil" class="form-label">Estado cívil</label>
        <select id="estadoCivil" name="estadoCivil" class="form-select form-control">
          <option disabled value="" selected>Selecionar</option>
          <option value="solteiro(a)">Solteiro(a)</option>
          <option value="casado(a)">Casado(a)</option>
          <option value="separado(a)">Separodo(a)</option>
          <option value="divorciado(a)">Divorciado(a)</option>
          <option value="viuvo(a)">Viuvo(a)</option>
      </select>
      </div>


      <div class="col-md-2">
        <label for="sexo" class="form-label">Sexo</label>
        <select id="sexo" name="sexo" class="form-select form-control">
          <option value="" disabled selected >Selecionar</option>
          <option value="M" >Masculino</option>
          <option value="F" >Feminino</option>
      </select>
      </div>

      <div class="col-md-3">
        <label for="escolaridade" class="form-label">Escolaridade</label>
        <select id="escolaridade" name="escolaridade" class="form-select form-control">
          <option value="" disabled selected >Selecionar</option>
          <option value="infantil">Educação infantil</option>
          <option value="fundamental">Fundamental</option>
          <option value="medio">Médio</option>
          <option value="superiorCursando">Superior(Graduação)</option>
          <option value="posGraduacao">Pós-graduação</option>
          <option value="mestrado">Mestrado</option>
          <option value="doutorado">Doutorado</option>
          <option value="escola">Escola</option>
      </select>
      </div>

      <div class="col-md-3">
        <label for="profissao" class="form-label">Profissão</label>
        <input id="profissao" name="profissao" type="text" class="form-control" placeholder="Estoquista">
      </div>

      <div class="col-md-2">
        <label for="renda" class="form-label">Renda</label>
        <input id="renda" name="renda" type="text" class="form-control" placeholder="1200">
      </div>

      <div class="col-md-2">
        <label for="telefone" class="form-label">Telefone</label>
        <input id="telefone" name="telefone" type="tel" class="form-control" placeholder="(11)1234-5678">
      </div>

      <div class="col-md-2">
        <label for="celular" class="form-label">Celular</label>
        <input id="celular" name="celular" type="tel" class="form-control" placeholder="(11)1234-5678">
      </div>

      <div class="col-md-2">
        <label for="telefoneRec" class="form-label">Telefone recado</label>
        <input id="telefoneRec" name="telRecado" type="tel" class="form-control" placeholder="(11)1234-5678">
      </div>
      
      <div class="col-md-4">
        <label for="e_mail" class="form-label">Email</label>
        <input id="e_mail" name="e_mail" type="email" class="form-control" placeholder="meu_email@gmail.com">
      </div>
      
      <div class="col-md-4">
        <label for="facebook" class="form-label">Facebook</label>
        <input id="facebook" name="facebook" type="text" class="form-control" placeholder="Nome de usuário">
      </div>
      
      <div class="col-md-3">
        <label for="idSocial" class="form-label">N°-NIS</label>
        <input id="idSocial" name="nis" type="text" class="form-control" placeholder="164.20509.09-3">
      </div>
      
      <div class="col-md-3">
        <label for="registroNasc" class="form-label">Número RG</label>
        <input id="registroNasc" name="rg" type="text" class="form-control" placeholder="00.568.456-1">
      </div>

      <div class="col-md-3">
        <label for="cpf" class="form-label">CPF</label>
        <input id="cpf" name="cpf" type="text" class="form-control" placeholder="005.680.456-12">
      </div>
      
      <div class="col-md-2">
        <label for="tituloEleitoral" class="form-label">Título Eleitoral</label>
        <input id="tituloEleitoral" name="titulo" type="text" class="form-control" placeholder="0012 5685 4561 78">
      </div>
      
      <div class="col-md-1">
        <label for="zonaEleitoral" class="form-label">Zona</label>
        <input id="zonaEleitoral" name="zonaEleitoral" type="text" class="form-control" placeholder="123">
      </div>

      <div class="col-md-2" style="margin-bottom: 50px;">
        <label for="sessaoEleitoral" class="form-label">Seção</label>
        <input id="sessaoEleitoral" name="sessaoEleitoral" type="text" class="form-control" placeholder="1234">
      </div>

      
      <div class="col-md-12">
        <button type="submit" class="btn btn-primary">Enviar</button>
      </div>
  </form>
</div>            



