(function( $ ) {
	var onMessage = [];
	var ws = new WebSocket('ws://' + location.host + '/ws');

	ws.onopen = function() {
	};

	ws.onmessage = function (evt) {
		var obj = jQuery.parseJSON( evt.data );
		for(var i = 0; i < onMessage.length; ++i) {
			onMessage[i].fn.call(onMessage[i].ctx, obj['module'], obj['action'], obj['data']);
		}
	};

	ws.onclose = function() {
		// websocket is closed.
	};

	$.ws = {
		'onMessage': function(fn, ctx) {
			onMessage.push({'fn': fn, 'ctx': ctx})
		}
	}
})( jQuery );
