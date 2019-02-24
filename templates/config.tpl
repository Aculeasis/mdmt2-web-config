<style>
%menu_style = "div.tab-frame input:nth-of-type({0}):checked ~ .tab:nth-of-type({0})"
%menu_styles = ",\n  ".join(menu_style.format(idx) for idx in range(1, len(tab_names) + 1))
  {{!menu_styles}}
  { display:block;}
</style>
<form action="/" method="post">
  <div class="tab-frame">
%for index, tab in enumerate(tab_names):
%index += 1
    <input class="hdn_input" type="radio"{{!" checked" if index == 1 else ""}} name="tab" id="tab{{!index}}">
    <label class="menu_label" for="tab{{!index}}">{{tab}}</label>
%end
%for section in sections:
{{!section}}
%end
  </div>
  <div class="buttons" id="send_buttons">
    <input type="submit"> <input type="reset"> <div class="version">v. {{!version}}</div>
  </div>
  <script language="javascript" type="text/javascript">handlerForThisRadio('{{!MAINTENANCE}}', 'send_buttons');</script>
</form>