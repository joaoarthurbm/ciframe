angular.module('deciframeApp').directive('dfHex', function() {
  return {
    restrict: 'E',
    scope: {
      acorde: '@',
      acordeColor: '@'
    },
    templateUrl: 'templates/directives/df-hex.html'
  }
});
