
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

    }
}


$('#dadosLogin').click(function(){

    dadosForm = $('#login').serialize();
    
    $.post('envioDados.php?'+dadosForm,function(data){
        console.log(data);
        if(data){
            $('#corpoDoSite').load('login.php');
        }
    });
    
});

$('#logout').click(function(){
    console.log('Saindo da pagina');
    window.location = 'logout.php';
});