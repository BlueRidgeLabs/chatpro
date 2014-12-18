controllers = angular.module('chat.controllers', []);

#============================================================================
# Helper function for building URLs
#============================================================================
chat_build_url = (path, params) ->
  ret = new Array
  for key, val of params
    if val?
      ret.push "#{key}=#{val}"
  path+'?'+ret.join '&'

#============================================================================
# Room controller
#============================================================================
controllers.controller 'RoomController', [ '$scope', '$http', '$timeout', ($scope, $http, $timeout) ->

  $scope.loading = false
  $scope.messages = []
  $scope.max_time = null
  $scope.min_time = null

  $scope.init = (room_id) ->
    $scope.room_id = room_id

    $scope.load_old_messages()

  $scope.load_old_messages = ->
    $scope.loading = true
    url = chat_build_url '/chat/message/', {room: $scope.room_id, before: $scope.min_time}
    $http.get url
    .success (data) ->
      # returned data has time fields that need parsed
      for msg in data.results
          msg.time = Date.parse msg.time

      $scope.min_time = Date.parse($scope.min_time)
      $scope.messages = data.results
      $scope.loading = false
]


