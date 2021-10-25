function navegacao(elemento){
    alert(elemento);
    
    $('#corpoDoSite').html('');

    if(elemento == 'sobre'){    
        
        $('#corpoDoSite').load('sobre.html');
    
    }else if(elemento == 'institucional'){
        $('#corpoDoSite').load('institucional.html');
    
    }else if(elemento == 'projetos'){
        $('#corpoDoSite').load('projetos.html');

    }
}