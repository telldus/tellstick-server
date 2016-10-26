var onMessage = [];

var WebSocketWrapper = function() {
	this.setup();
}

WebSocketWrapper.prototype.setup = function() {
	this.ws = new WebSocket('ws://' + location.host + '/ws');
	this.ws.onopen = function() {
		//console.log("Websocket opened");
	};

	this.ws.onmessage = function (evt) {
		var obj = JSON.parse( evt.data );
		for(var i = 0; i < onMessage.length; ++i) {
			onMessage[i].messageReceived(obj['module'], obj['action'], obj['data']);
		}
	};

	this.ws.onclose = function() {
		// websocket is closed.
		//console.log("Websocket closed");
	};
}

WebSocketWrapper.prototype.register = function (evt) {
	onMessage.push(evt);
};

WebSocketWrapper.prototype.unregister = function (evt) {
	var index = onMessage.indexOf(evt)
	if (index >= 0) {
		onMessage.splice(index, 1);
	}
};

var ws = new WebSocketWrapper();

var WebSocketInstance = function() {
	this.filter = [];
}

WebSocketInstance.prototype.messageReceived = function(module, action, data) {
	for(var i = 0; i < this.filter.length; ++i) {
		if (this.filter[i].module === module && this.filter[i].action === action) {
			this.filter[i].fn(module, action, data);
		}
	}
}

WebSocketInstance.prototype.onMessage = function (module, action, evt) {
	if (evt == null) {
		for(var i = 0; i < this.filter.length; ++i) {
			if (this.filter[i].module === module && this.filter[i].action === action) {
				this.filter.splice(i, 1);
				break;
			}
		}
		if (this.filter.length == 0) {
			ws.unregister(this);
		}
	} else {
		if (this.filter.length == 0) {
			ws.register(this);
		}
		this.filter.push({module: module, action: action, fn: evt});
	}
};

export default () => WebSocketInstance
