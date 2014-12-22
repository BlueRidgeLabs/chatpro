filters = angular.module('chat.filters', []);

filters.filter 'unread', [ ->
  (count) ->
    if parseInt(count) >= 100 then '99+' else count
]
