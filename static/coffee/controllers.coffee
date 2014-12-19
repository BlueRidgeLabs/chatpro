controllers = angular.module('chat.controllers', ['chat.services']);

parse_iso8601 = (str) ->
  if str then new Date(Date.parse str) else null

#============================================================================
# Chat controller (loads new messages for all rooms)
#============================================================================
controllers.controller 'ChatController', [ '$scope', '$http', '$timeout', 'MessageService', ($scope, $http, $timeout, MessageService) ->

  $scope.init = () ->
    $scope.fetchNewMessages()

  $scope.fetchNewMessages = () ->
    MessageService.fetchNewMessages ->
      $timeout($scope.fetchNewMessages, 5000)
]

#============================================================================
# Room controller (loads old messages)
#============================================================================
controllers.controller 'RoomController', [ '$scope', '$http', 'MessageService', ($scope, $http, MessageService) ->

  $scope.new_message = ''
  $scope.sending = false
  $scope.loading_old = false
  $scope.messages = []
  $scope.oldest_time = null
  $scope.has_older = true

  $scope.init = (room_id) ->
    $scope.room_id = room_id
    $scope.load_old_messages()

    MessageService.onNewMessages (messages) ->
      # extract messages for this room
      room_messages = []
      for msg in messages:
        if msg.room_id = $scope.room_id
          room_messages.append msg

      # TODO display new messages

      console.log('room #' + $scope.room_id + " new messages " + room_messages)

  # TODO move functionality to MessageService

  $scope.send_new_message = ->
    $scope.sending = true

    data = new FormData();
    data.append('room', $scope.room_id)
    data.append('text', $scope.new_message)
    $http.post '/message/send/?', data, {
            transformRequest: angular.identity,
            headers: {'Content-Type': undefined}
    }
    .success (data) ->
      console.log(data)

    $scope.new_message = ''
    $scope.sending = false

  $scope.load_old_messages = ->
    $scope.loading_old = true

    if $scope.oldest_time
      # TODO provide backup when browser doesn't support toISOString
      before = $scope.oldest_time.toISOString()
    else
      before = new Date().toISOString()

    $http.get '/message/?' + $.param({room: $scope.room_id, before: before})
    .success (data) ->
      # returned data has time fields that need parsed
      for msg in data.results
          msg.time = parse_iso8601 msg.time

      $scope.oldest_time = parse_iso8601 data.oldest_time
      $scope.has_older = data.has_older

      Array::push.apply $scope.messages, data.results

      $scope.loading_old = false
]
