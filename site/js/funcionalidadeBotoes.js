
function navegacao(elemento){
    
    $('#corpoDoSite').html('');

    if(elemento == 'sobre'){    
        
        $('#corpoDoSite').load('sobre.html');
    
    }else if(elemento == 'institucional'){
        $('#corpoDoSite').load('institucional.html');
    
    }else if(elemento == 'projetos'){
        $('#corpoDoSite').load('projetos.html');

    }else if(elemento == 'associados'){
        $('#corpoDoSite').load('login.html');

    }
}


$('#dadosLogin').click(function(){

    console.log('funcionou!!!');
});