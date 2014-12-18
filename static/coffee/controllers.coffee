controllers = angular.module('chat.controllers', []);

parse_iso8601 = (str) ->
  if str then new Date(Date.parse str) else null

#============================================================================
# Room controller
#============================================================================
controllers.controller 'RoomController', [ '$scope', '$http', '$timeout', ($scope, $http, $timeout) ->

  $scope.loading = false
  $scope.messages = []
  $scope.newest_time = null
  $scope.oldest_time = null
  $scope.has_older = true

  $scope.init = (room_id) ->
    $scope.room_id = room_id

    $scope.load_old_messages()

  $scope.load_old_messages = ->
    $scope.loading = true

    params = {room: $scope.room_id}
    if $scope.min_time
      # TODO provide backup when browser doesn't support toISOString
      params['before'] = $scope.min_time.toISOString()

    $http.get '/chat/message/?' + $.param(params)
    .success (data) ->
      # returned data has time fields that need parsed
      for msg in data.results
          msg.time = parse_iso8601 msg.time

      $scope.max_time = parse_iso8601 data.newest_time

      $scope.min_time = parse_iso8601 data.oldest_time
      $scope.has_older = data.has_older

      Array::push.apply $scope.messages, data.results

      $scope.loading = false
]


