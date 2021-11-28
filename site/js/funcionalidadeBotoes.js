
function navegacao(elemento){
    
    $('#corpoDoSite').html('');

    if(elemento == 'sobre'){    
        
        $('#corpoDoSite').load('sobre.html');
    
    }else if(elemento == 'institucional'){
        $('#corpoDoSite').load('institucional.html');
    
    }else if(elemento == 'projetos'){
        $('#corpoDoSite').load('projetos.html');

    }else if(elemento == 'cadastrar'){
        $('#corpoDoSite').load('cadastro.php');

    }else if(elemento == 'consultar'){
        $('#corpoDoSite').load('consulta.php');

    }else if(elemento == 'cadastrarADM'){
        $('#corpoDoSite').load('cadastrarADM.php');

    }
}


$('#dadosLogin').click(function(){
    console.log('clicou');
    dadosForm = $('#login').serialize();
    
    $.post('envioDados.php?'+dadosForm,function(data){
        
        var dados = JSON.parse(data);
        console.log(dados['statos']);
        console.log(dados['pagina']);
        if(dados['statos']){
            $('#corpoDoSite').load(dados['pagina']);
        }else{
            alert('Usuário e ou senha invalidos !');
        }
    });
    
});

$('#logout').click(function(){
    console.log('Saindo da pagina');
    window.location = 'logout.php';
});