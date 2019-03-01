%if wiki:
<p><label class="key_label"><abbr title="{{wiki}}">{{key}}</abbr></label>
%else:
<p><label class="key_label">{{key}}</label>
%end
%if isinstance(value, bool):
<select name="{{section}}${{key}}">
  <option value="1"{{" selected " if value else " "}}>on</option>
  <option value="0"{{" selected " if not value else " "}}>off</option>
</select></p>
%elif isinstance(value, int):
<input type="number" name="{{section}}${{key}}" value="{{value}}"></p>
%elif isinstance(value, str):
<input type="text" name="{{section}}${{key}}" value="{{value}}"></p>
%elif isinstance(value, float):
<input type="number" step="0.01" name="{{section}}${{key}}" value="{{value}}"></p>
%else:
%type__ == type(value)
{{name}}: <p>Unknown type: "{{type__}}"</p>
%end