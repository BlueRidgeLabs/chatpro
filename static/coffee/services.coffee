services = angular.module('chat.services', []);

#=====================================================================
# Date utilities
#=====================================================================
parse_iso8601 = (str) ->
  if str then new Date(Date.parse str) else null

format_iso8601 = (date) ->
  # TODO provide backup when browser doesn't support toISOString
  if date then date.toISOString() else null

#=====================================================================
# Room service
#=====================================================================
services.factory 'RoomService', ['$rootScope', '$http', ($rootScope, $http) ->
  new class RoomService

    #=====================================================================
    # Broadcasts event to signal that active room has changed
    #=====================================================================
    activateRoom: (room_id) ->
      $rootScope.$broadcast 'room_activated', room_id

    #=====================================================================
    # Registers a callback for active room changes
    #=====================================================================
    onActivateRoom: (callback) ->
      $rootScope.$on('room_activated', (event, room_id) -> callback(parseInt room_id))

    #=====================================================================
    # Fetches all contacts, users and managers for this room
    #=====================================================================
    fetchParticipants: (room_id, callback) ->
      $http.get('/room/participants/' + room_id + '/')
      .success (data) =>
        callback(data.results)
]


#=====================================================================
# Message service
#=====================================================================
services.factory 'MessageService', ['$rootScope', '$http', '$timeout', ($rootScope, $http, $timeout) ->
  new class MessageService
    constructor: ->
      @start_time = new Date()
      @max_id = null
      @room_min_ids = {}
      @pending_ids = []

      $timeout((=> @fetchNewMessages()), 1000)
      $timeout((=> @refreshPendingMessages()), 1000)

    #=====================================================================
    # Fetches new messages for all rooms
    #=====================================================================
    fetchNewMessages: ->
      # first fetch is for messages after start time. Subsequent fetches use the last returned max id
      params = if @max_id then {after_id: @max_id} else {after_time: format_iso8601 @start_time}

      $http.get '/message/?' + $.param(params)
      .success (data) =>
        if data.results.length > 0
          @max_id = data.max_id
          room_messages = @processMessages data.results

          # broadcast event for each room
          for room_id of room_messages
            $rootScope.$broadcast 'new_messages', room_id, room_messages[room_id]
      .then =>
        $timeout((=> @fetchNewMessages()), 5000)

    #=====================================================================
    # Registers a callback for new messages
    #=====================================================================
    onNewMessages: (callback) ->
      $rootScope.$on('new_messages', (event, room_id, messages) -> callback(parseInt(room_id), messages))

    #=====================================================================
    # Fetches old messages for the given room
    #=====================================================================
    fetchOldMessages: (room_id, callback) ->
      params = {room: room_id}

      # first fetch is for messages before start time. Subsequent fetches use the last returned min id
      min_id = @room_min_ids[room_id]
      if min_id
        params['before_id'] = min_id
      else
        params['before_time'] = format_iso8601 @start_time

      $http.get '/message/?' + $.param(params)
      .success (data) =>
        @room_min_ids[room_id] = data.min_id

        room_messages = @processMessages data.results

        messages = if room_messages[room_id]? then room_messages[room_id] else []
        callback(messages, data.has_older)

    #=====================================================================
    # Refreshes pending messages for all rooms
    #=====================================================================
    refreshPendingMessages: ->
      if @pending_ids.length > 0
        $http.get '/message/?ids=' + @pending_ids.join(',')
        .success (data) =>
          # extract no-longer-pending messages
          sent_messages = []
          for msg in data.results
            if msg.status == 'S'
              sent_messages.push msg
              @pending_ids.splice(@pending_ids.indexOf(msg.id), 1)

          room_messages = @processMessages sent_messages

          # broadcast event for each room
          for room_id of room_messages
            $rootScope.$broadcast 'messages_sent', room_id, room_messages[room_id]

        .then =>
          $timeout((=> @refreshPendingMessages()), 5000)
      else
        $timeout((=> @refreshPendingMessages()), 5000)

    #=====================================================================
    # Registers a callback for message send status changes
    #=====================================================================
    onMessagesSent: (callback) ->
      $rootScope.$on('messages_sent', (event, room_id, messages) -> callback(parseInt(room_id), messages))

    #=====================================================================
    # Sends a message to the given room
    #=====================================================================
    sendMessage: (room_id, text, user_id, user_name, callback) ->
      # notify room to add as temp message immediately
      temp_msg = {
        sender: {
          id: user_id,
          type: 'U',
          full_name: user_name
        }, text: text,
        room_id: room_id,
        temp: true
      }
      $rootScope.$broadcast 'new_messages', room_id, [temp_msg]

      data = new FormData();
      data.append('text', text)
      data.append('room', room_id)
      $http.post '/message/send/?', data, {
              transformRequest: angular.identity,
              headers: {'Content-Type': undefined}
      }
      .success (data) ->
        callback(data)

    #=====================================================================
    # Processes incoming messages, organizing by room
    #=====================================================================
    processMessages: (messages) ->
      room_messages = {}

      for msg in messages
        # parse datetime string
        msg.time = parse_iso8601 msg.time

        # simplify figuring out which messages are from contacts vs users
        msg.from_contact = msg.sender.type == 'C'
        msg.from_user = msg.sender.type == 'U'

        # track pending messages
        if msg.status == 'P'
          @pending_ids.push msg.id

        # organize messages by room
        if !room_messages[msg.room_id]?
          room_messages[msg.room_id] = []
        room_messages[msg.room_id].push msg

      room_messages
]
