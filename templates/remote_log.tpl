<!-- remote_log -->
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
</style>
<div>
    <p>
        <input type="button" name=clearButton value="Clear" onClick="clearText();">
        <input type="button" name=connectButton value="Connect" id="connectButton" onClick="doConnectDisconnect();">
    </p>
</div>
<div id="log_outputtext" class="log_outputtext"></div>

<script language="javascript" type="text/javascript">
    var remote_log = document.getElementById("log_outputtext");
    var connectButton = document.getElementById("connectButton");
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
  function doConnect()
  {
    websocket = new WebSocket("ws://{{!terminal_ip}}:7999/");
    websocket.onopen = function(evt) { onOpen(evt) };
    websocket.onclose = function(evt) { onClose(evt) };
    websocket.onmessage = function(evt) { onMessage(evt) };
    websocket.onerror = function(evt) { onError(evt) };
  }
  function onOpen(evt)
  {
    writeToScreenMsg("connected");
    connectButton.value = "Disconnect";
    websocket.send('{{!terminal_ws_token}}');
    websocket.send('remote_log');
  }
  function onClose(evt)
  {
    writeToScreenMsg("disconnected");
    connectButton.value = "Connect";
  }
  function onMessage(evt)
  {
    writeToScreenLog(evt.data);
  }
  function onError(evt)
  {
    writeToScreenMsg('error: ' + evt.data);
    websocket.close();
  }
  function writeToScreenMsg(message)
  {
    writeToScreen('<span style="color: darkorange">' + message + '</span>');
  }
  function writeToScreenLog(message)
  {
    writeToScreen(ansispan(safe_tags_replace(message)));
  }
  function writeToScreen(message)
  {
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
</script>
</div>
<!-- remote_log end -->