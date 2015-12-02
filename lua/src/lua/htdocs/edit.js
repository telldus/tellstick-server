$(document).ready(function() {
	var editor = CodeMirror.fromTextArea(document.getElementById("code"), {
		matchBrackets: true,
		theme: "neat",
		lineNumbers: true,
		indentWithTabs: true
	});
	$.ws.onMessage(function(module, action, data) {
		if (module == 'lua' && action == 'log') {
			$('#log').append('<p>' + data + '</p>');
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
});
