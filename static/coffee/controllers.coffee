controllers = angular.module('chat.controllers', ['chat.services']);

#============================================================================
# Chat controller
#============================================================================
controllers.controller 'ChatController', [ '$scope', 'MessageService', ($scope, MessageService) ->

  $scope.init = (user_id, user_name) ->
    $scope.user_id = user_id
    $scope.user_name = user_name
]

#============================================================================
# Room controller
#============================================================================
controllers.controller 'RoomController', [ '$scope', '$http', 'MessageService', ($scope, $http, MessageService) ->

  $scope.new_message = ''
  $scope.sending = false
  $scope.loading_old = false
  $scope.messages = []
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
  # Sends a new message
  #============================================================================
  $scope.sendNewMessage = ->
    $scope.sending = true

    # prepend as temp message immediately
    $scope.messages.unshift {
      user_id: $scope.user_id,
      contact_id: null,
      sender_name: $scope.user_name,
      text: $scope.new_message,
      room_id: $scope.room_id,
      temp: true
    }

    MessageService.sendMessage $scope.room_id, $scope.new_message, ->
      $scope.new_message = ''
      $scope.sending = false

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
