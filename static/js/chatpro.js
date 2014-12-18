/**
 * Function library
 */
(function(chatpro, $) {
    /**
     * Builds a URL
     */
    chatpro.build_url = function(resource, params) {
        var ret = resource + "?";
		if (params) {
			for (key in params) {
				var val = params[key];
				if (val != null) {
					if ($.isPlainObject(val)) { // if value is an object then serialize it
						val = $.param(val);
					}
					ret += key + '=' + encodeURIComponent(val) + '&';
				}
			}
		}
		return ret;
    };
}( window.chatpro = window.chatpro || {}, jQuery ));

/**
 * Angular configuration
 *
 * Since Django uses {{ }}, we will have angular use [[ ]] instead.
 */
var app = angular.module('chat', []);
app.config(function($interpolateProvider) {
    $interpolateProvider.startSymbol('[[');
    $interpolateProvider.endSymbol(']]');
});

/**
 * Controller for room panel
 */
app.controller('RoomController', ['$scope', '$http', function($scope, $http) {
    $scope.loading = false;
    $scope.messages = [];
    $scope.max_time = null;
    $scope.min_time = null;

    $scope.init = function(room_id) {
        $scope.room_id = room_id;

        $scope.load_old_messages();
    };

    $scope.load_old_messages = function() {
        $scope.loading = true;
        var url = chatpro.build_url('/chat/message/', {room: $scope.room_id, before: $scope.min_time});
        $http.get(url).success(function(data) {
            // returned data has time fields that need parsed
            for (var m = 0; m < data.results.length; m++) {
                var msg = data.results[m];
                msg.time = Date.parse(msg.time);
            }
            $scope.min_time = Date.parse($scope.min_time);
            $scope.messages = data.results;
            $scope.loading = false;
        });
    };
}]);