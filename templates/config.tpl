<style>
%menu_style = "div.tab-frame input:nth-of-type({0}):checked ~ .tab:nth-of-type({0})"
%menu_styles = ",\n  ".join(menu_style.format(idx) for idx in range(1, len(tab_names) + 1))
  {{!menu_styles}}
  { display:block;}
</style>
<form action="/" method="post">
  <div class="tab-frame">
%index = 1
%checked = " checked "
%for tab in tab_names:
    <input class="hdn_input" type="radio"{{!checked}}name="tab" id="tab{{!index}}"><label class="menu_label" for="tab{{!index}}">{{tab}}</label>
%index += 1
%checked = " "
%end
%for section in sections:
{{!section}}
%end
  </div>
  <p><input type="submit"> <input type="reset"></p>
</form>