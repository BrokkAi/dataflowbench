const params = new URLSearchParams(window.location.search);
const data = params.get("data");
JSON.parse(data);
