<?php
    ########################################################
    $server = '********';
    $user = '*****';
    $password = '*******';
    $database = '****';
    $port = '****';
    ########################################################


$db = pg_connect("host=$server port=$port dbname=$database user=$user password=$password");

  if (!$db) {
      echo pg_last_error($db);
  }
 
?>
