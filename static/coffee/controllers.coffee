controllers = angular.module('chat.controllers', ['chat.services']);

#============================================================================
# Chat controller
#============================================================================
controllers.controller 'ChatController', [ '$scope', 'MessageService', ($scope, MessageService) ->

  $scope.active_room_id = null
  $scope.new_message = ''
  $scope.sending = false

  $scope.init = (user_id, user_name, initial_room_id) ->
    $scope.user_id = user_id
    $scope.user_name = user_name
    $scope.active_room_id = initial_room_id

  $scope.showRoom = (room_id) ->
    $scope.active_room_id = room_id

  #============================================================================
  # Sends a new message to the active room
  #============================================================================
  $scope.sendMessage = ->
    $scope.sending = true

    MessageService.sendMessage $scope.active_room_id, $scope.new_message, $scope.user_id, $scope.user_name, ->
      $scope.new_message = ''
      $scope.sending = false

]

#============================================================================
# Room controller
#============================================================================
controllers.controller 'RoomController', [ '$scope', '$http', 'MessageService', ($scope, $http, MessageService) ->

  $scope.messages = []
  $scope.loading_old = false
  $scope.has_older = true

  $scope.init = (room_id) ->
    $scope.room_id = room_id
    $scope.loadOldMessages()

    MessageService.onNewMessages (room_id, messages) ->
      if room_id == $scope.room_id
        # remove temp messages
        non_temp_messages = []
        for msg in $scope.messages
          if !msg.temp
            non_temp_messages.push msg

        # prepend new messages
        $scope.messages = messages.concat non_temp_messages

  #============================================================================
  # Loads old messages - called by infinite scroller
  #============================================================================
  $scope.loadOldMessages = ->
    $scope.loading_old = true

    MessageService.fetchOldMessages $scope.room_id, (messages, has_older) ->
      $scope.messages = $scope.messages.concat messages
      $scope.has_older = has_older
      $scope.loading_old = false
]
