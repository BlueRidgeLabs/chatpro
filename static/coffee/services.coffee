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
    fetchProfiles: (room_id, callback) ->
      $http.get('/room/profiles/' + room_id + '/')
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

      $timeout(=> @fetchNewMessages())

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

          messages = @processMessages data.results

          # organize messages by room
          room_messages = {}
          for msg in messages
            if !room_messages[msg.room_id]?
              room_messages[msg.room_id] = []
            room_messages[msg.room_id].push msg

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
        messages = @processMessages data.results

        @room_min_ids[room_id] = data.min_id

        callback(messages, data.has_older)

    #=====================================================================
    # Sends a message to the given room
    #=====================================================================
    sendMessage: (room_id, text, user_id, user_name, callback) ->
      # notify room to add as temp message immediately
      temp_msg = { user_id: user_id, contact_id: null, sender_name: user_name, text: text, room_id: room_id, temp: true }
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
    # Processes incoming messages (parses the date strings)
    #=====================================================================
    processMessages: (messages) ->
      for msg in messages
        msg.time = parse_iso8601 msg.time
      messages
]
