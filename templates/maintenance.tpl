<!-- maintenance -->
<div class="tab">
<hr>
<style>
    .log_outputtext {
    background-color: black;
    color: aliceblue;
    overflow-y: auto;
    overflow-x: hidden;
    max-width: 1000px;
    height: 500px;
    font-family: monospace;
    font-size: 12px;
    border-color: black;
    padding: 2px;
    border-width: thick;
    border-style: solid;
    }
    .model_button {
      width: 5em;
    }
    .model_block {
      border: dotted;
      border-width: thin;
      margin-top: 0.5em;
      margin-bottom: 0.5em;
      padding-left: 0.6em;
      padding-right: 0.6em;
    }
    .model_label {
      width: 4em;
    }
</style>
<!-- remote_log -->
<div>
    <p>
        <input type="button" name=clearButton value="Clear" onClick="clearText();">
        <input type="button" name=connectButton value="Connect" id="connectButton" onClick="doConnectDisconnect();">
    </p>
</div>
<div id="log_outputtext" class="log_outputtext"></div>
<!-- remote_log end -->
<!-- actions -->
<div class="model_block">
    <!-- models -->
    <div class="model_block">
        <p>
            <label class="model_label">Model:</label>
            <input type="button" class="model_button" name=compileButton value="Compile" onClick="sendRecCMD('compile');">
            <input type="button" class="model_button" name=removeButton value="Remove" onClick="sendRecCMD('del');">
            <select id="modelSelect">
                <option value="1">1</option><option value="2">2</option><option value="3">3</option>
                <option value="4">4</option><option value="5">5</option><option value="6">6</option>
            </select>
        </p>
        <p>
            <label class="model_label">Sample:</label>
            <input type="button" class="model_button" name=recordButton value="Record" onClick="sendRecCMD('rec');">
            <input type="button" class="model_button" name=playButton value="Play" onClick="sendRecCMD('play');">
            <select id="sampleSelect">
                <option value="1">1</option><option value="2">2</option><option value="3">3</option>
            </select>
        </p>
    </div>
    <!-- models end -->
    <!-- send commands -->
    <div class="model_block">
        <p>
            <label class="model_label">CMD:</label>
            <input type="button" class="model_button" name="cmdButton" value="Send" onclick="sendCMD();">
            <select id="cmdSelect">
                <option value="maintenance.reload">Reload</option><option value="maintenance.stop">Stop</option>
                <option value="listener:on">Listener On</option><option value="listener:off">Listener Off</option>
            </select>
        </p>
    </div>
    <!-- send commands end -->
</div>
<!-- actions end -->
<script language="javascript" type="text/javascript">
    var server_url = "ws://{{!terminal_ip}}:7999/";
    var server_token = "{{!terminal_ws_token}}";
    var authorization = '{"method":"authorization","params":["{{!auth_token}}"],"id":"Authorization"}';

    var remote_log = document.getElementById("log_outputtext");
    var connectButton = document.getElementById("connectButton");

    var model_select = document.getElementById("modelSelect");
    var sample_select = document.getElementById("sampleSelect");
    var cmd_select = document.getElementById("cmdSelect");


    function sendRecCMD(cmd) {
      commandExecutor("rec:"+cmd+"_"+model_select.value+"_"+sample_select.value);
    }

    function sendCMD() {
      commandExecutor(cmd_select.value);
    }

    function commandExecutor(line) {
      var ws = new WebSocket(server_url);
      ws.onerror = function(evt) {
        console.log('error on "' + line + '": ' + evt.data);
      };
      ws.onopen = function() {
        ws.send(server_token);
        ws.send(authorization);
      };
      ws.onmessage = function(evt) {
        console.log('execute: ' + line);
        ws.send(line);
        ws.close();
      };
    }

    // ansi color -> html; https://github.com/mmalecki/ansispan
    var ansispan = function (str) {
      Object.keys(ansispan.foregroundColors).forEach(function (ansi) {
        var span = '<span style="color: ' + ansispan.foregroundColors[ansi] + '">';
        str = str.replace(
          new RegExp('\033\\[' + ansi + 'm', 'g'),
          span
        ).replace(
          new RegExp('\033\\[1;' + ansi + 'm', 'g'),
          span
        );
      });
      return restoreURI(str.replace(/\033\[0m/g, '</span>'));
    };
    ansispan.foregroundColors = {
      '36': 'cyan',
      '90': 'gray',
      '92': 'mediumspringgreen',
      '93': 'yellow',
      '91': 'red',
      '95': 'darkred'
    };
    // replace start
    var tagsToReplace = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;'
    };
    function replaceTag(tag) {
        return tagsToReplace[tag] || tag;
    }
    function safe_tags_replace(str) {
        return str.replace(/[&<>]/g, replaceTag);
    }
    function restoreURI(str) {
        return str.includes('<span style="color: cyan">majordomo</span>') ? decodeURI(str) : str;
    }
    // replace end
  function doConnect() {
    websocket = new WebSocket(server_url);
    websocket.onopen = function(evt) { onOpen(evt) };
    websocket.onclose = function(evt) { onClose(evt) };
    websocket.onmessage = function(evt) { onMessage(evt) };
    websocket.onerror = function(evt) { onError(evt) };
  }
  function onOpen(evt) {
    writeToScreenMsg("connected");
    connectButton.value = "Disconnect";
    websocket.send(server_token);
    websocket.send(authorization);
    websocket.send('remote_log');
  }
  function onClose(evt) {
    writeToScreenMsg("disconnected");
    connectButton.value = "Connect";
  }
  function onMessage(evt) {
    if (evt.data.startsWith('{') && evt.data.endsWith('}')) {
      let msg = JSON.parse(evt.data);
      writeToScreenMsg(safe_tags_replace(`${msg.id} ${msg.result}`));
      return;
    };
    writeToScreenLog(evt.data);
  }
  function onError(evt) {
    writeToScreenMsg('error: ' + evt.data);
    websocket.close();
  }
  function writeToScreenMsg(message) {
    writeToScreen('<span style="color: darkorange">' + message + '</span>');
  }
  function writeToScreenLog(message) {
    writeToScreen(ansispan(safe_tags_replace(message)));
  }
  function writeToScreen(message) {
    remote_log.innerHTML += message + "<br>";
    remote_log.scrollTop = remote_log.scrollHeight;
  }
  function clearText() {
    remote_log.innerHTML = "";
  }
  function doDisconnect() {
    websocket.close();
  }
  function doConnectDisconnect() {
    (connectButton.value == "Connect") ? doConnect() : doDisconnect()
  }
  function handlerForThisRadio(searchText, onOFF) {
    var labels = document.getElementsByTagName("label");
    var element = document.getElementById(onOFF);
    if (!element) return;

    for (var i = 0; i < labels.length; i++) {
      if (!labels[i].htmlFor) continue;
      var radio = document.getElementById(labels[i].htmlFor);
      if (!radio) continue;
      if (labels[i].textContent == searchText) {
        radio.onchange = function() {
          element.style.visibility = 'hidden';
        };
        if (radio.checked) element.style.visibility = 'hidden';
      } else {
        radio.onchange = function() {
          element.style.visibility = 'visible';
        }
      }
    }
  }
</script>
</div>
<!-- maintenance end -->