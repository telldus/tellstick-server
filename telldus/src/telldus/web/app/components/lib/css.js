export default function() {
	return {
		load: function (name, parentRequire, onload, config) {
			var link = document.createElement("link");
			link.type = "text/css";
			link.rel = "stylesheet";
			link.href = name;
			document.getElementsByTagName("head")[0].appendChild(link);
			onload(null);
		}
	}
}
