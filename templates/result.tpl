<h3>Changes in settings:</h3>
<xmp class="result">{{!result}}</xmp>
<form action="/{{!"less" if less else "more"}}" method="post">
 <input type="hidden" name="_this_is_get_no_post">
 <div class="buttons"><input type="submit" value="Back" />
  <div class="version">v. {{!version}} | <a class="mode" href="/{{!"more" if less else "less"}}">{{!"more" if less else "less"}}</a> |</div></div>
</form>