<?php

require_once 'config/Configuration.php';
include_once __DIR__ .'/vendor/autoload.php';

spl_autoload_register(function ($class){

    $file =  __DIR__ . '/Engine/'. $class .'.php';

    if (file_exists($file)){
        include_once $file;
    }

});

Session::startSession();
Cookie::init();
$db = Database::getInstance();

$login = new Login();

