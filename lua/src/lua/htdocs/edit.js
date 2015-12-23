$(document).ready(function() {
	var codeElement = document.getElementById("code");
	if (codeElement) {
		var editor = CodeMirror.fromTextArea(codeElement, {
			matchBrackets: true,
			theme: "neat",
			lineNumbers: true,
			indentWithTabs: true,
			indentUnit: 4,
			tabSize: 4
		});
	}
	$.ws.onMessage(function(module, action, data) {
		if (module == 'lua' && action == 'log') {
			$('#log').append($('<p>').text(data));
			$('#log').animate({
				scrollTop: $('#log').height()
			}, 300);
			var elem = document.getElementById('log');
			elem.scrollTop = elem.scrollHeight;
		}
	});
	$('#save').on('click', function() {
		editor.save();
		$.post(
			'/lua/save',
			$( "#codeForm" ).serialize()
		).done(function() {
		});
	})
	$('#clearLog').on('click', function() {
		$('#log').empty();
	})
	$('#newScript').on('click', function() {
		var scriptName = prompt('Enter name of new script.\nAllowed chars: a-z, A-Z, 0-9 and -');
		if (!scriptName) {
			return;
		}
		$.post(
			'/lua/new',
			{'name': scriptName}
		).done(function() {
			alert('New file created. Please reload page to see it in the menu');
		});
	});
});
