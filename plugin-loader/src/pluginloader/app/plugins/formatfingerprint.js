define([], function() {
	return fingerprint => {
		if (typeof(fingerprint) != 'string') {
			return '';
		}
		return fingerprint.match(/.{1,4}/g).join(' ');
	};
});
