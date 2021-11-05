<?php 

    try 
    {   $user = 'root';
        $pass = '';
        $dbname = 'projetointegrador';
        $host = '127.0.0.1';
        $db = new PDO( "mysql:host=$host;dbname=$dbname;charset=utf8", $user, $pass )
            or die("Error");
    }
    catch(PDOException $e)
    {
        header("location: index.php");
    }

?>