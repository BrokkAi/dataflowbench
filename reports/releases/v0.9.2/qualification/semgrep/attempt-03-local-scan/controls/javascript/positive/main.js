const params = new URLSearchParams(window.location.search);
const code = params.get("code");
eval(code);
