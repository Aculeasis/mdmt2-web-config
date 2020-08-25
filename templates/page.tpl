<!DOCTYPE html>
<html>
<head>
  <title>mdmTerminal2 Web Config</title>
  <meta charset="utf-8">
  <link rel="icon" type="image/png" href="/img/favicon-32x32.png">
</head>
<body>
<style>
  .hdn_input { display:none;}
  div.tab-frame label{ display:block; float:left;}
  div.tab-frame input:checked + label{ background:black; color:white; cursor:default}
  div.tab-frame div.tab{ display:none; padding:5px 10px;clear:left}
  .key_label {
     padding-right: 4px;
     min-width: 11em;
  }
  .menu_label {
     padding: 5px 10px;
     cursor: pointer;
  }
  .result {
    background: #f8f7f2;
  }
  .version {
    font-size: xx-small;
    float: right;
    position: relative;
    right: 5%;
    transform: translate(0, 50%);
    visibility: visible;
  }
  .buttons {
    padding-left: 0.5em;
  }
  body{max-width:800px;margin:20px auto;font-family:Arial;}
  .mode {
    color: #6991df;
    font-size: small;
    font-weight: bold;
  }
</style>
{{!body}}
</body>
</html>