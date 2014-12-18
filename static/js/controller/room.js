
var app = angular.module('chat', []);

app.config(function($interpolateProvider) {
    $interpolateProvider.startSymbol('[[');
    $interpolateProvider.endSymbol(']]');
});

app.controller('RoomController', ['$scope', '$http', function($scope, $http) {
    $scope.messages = [];
    $scope.earliest_time = null;

    $scope.init = function(room_id) {
        $scope.room_id = room_id;

        $scope.fetch_messages();
    };

    $scope.fetch_messages = function() {
        messages_url = '/chat/message/?room=' + $scope.room_id;
        $http.get(messages_url).success(function(data) {
            for (var m = 0; m < data.results.length; m++) {
                var msg = data.results[m];
                msg.time = Date.parse(msg.time);
            }
            $scope.messages = data.results;
            $scope.earliest_time = $scope.earliest_time;
        });
    };
}]);