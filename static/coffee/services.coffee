services = angular.module('chat.services', []);

parse_iso8601 = (str) ->
  if str then new Date(Date.parse str) else null

services.factory 'MessageService', ['$rootScope', '$http', ($rootScope, $http) ->
  new class MessageService
    constructor: ->
      @newest_time = new Date()

    fetchNewMessages: (callback) ->
      $http.get '/message/?' + $.param({after: @newest_time.toISOString()})
      .success (data) ->
        if data.results.length > 0
          @newest_time = parse_iso8601 data.newest_time

          # returned data has time fields that need parsed
          for msg in data.results
              msg.time = parse_iso8601 msg.time

          $rootScope.$broadcast('new_messages', data.results)
      .then ->
        callback()

    onNewMessages: (callback) ->
      $rootScope.$on('new_messages', callback)
]
