<?php 
  session_start();
  //print_r($_SESSION);
  if(empty($_SESSION['Cod_Usuario'])){
      
      $_SESSION['paginaAtual'] = 'cadastrarADM.php';
      header('location:login.php');
  }
?>

<div style="font-size: x-large; margin-left: auto;
    margin-right: 15px;
    margin-top: 100px;
    margin-block-end: 50px;">
  <form class="row g-3" style="margin-left: 30px;" action="cadastroDadosADM.php" method="POST">
      
      <div class="col-md-8">
        <label for="nomeCompleto" class="form-label">Nome do administrador</label>
        <input name="nome" class="form-control" type="text" id="nomeCompleto" placeholder="Nome completo" >
      </div>

      <div class="col-md-8">
        <label for="email" class="form-label">Email</label>
        <input name="email" class="form-control" type="text" id="email" placeholder="meu_email@gmail.com" >
      </div>
      
      <div class="col-md-8">
        <label for="senha" class="form-label">Definir uma senha</label>
        <input name="senha" class="form-control" type="password" id="senha">
      </div>
      
      <div class="col-md-8">
        <label for="tipoUsuario" class="form-label">Tipo de administrador</label>
        <select id="tipoUsuario" name="tipoUsuario" class="form-select form-control">
          <option value="10">Secretário(a)</option>
          <option value="20">Gerente</option>
          <option value="30">Desenvolvedor</option>
          <option value="40">Presidência</option>
      </select>
      </div>

      
      <div class="col-md-12">
        <button type="submit" class="btn btn-primary">Enviar</button>
      </div>
  </form>
</div>            



