angular.module('deciframeApp').directive('dfEsfinge', function() {
  return {
    restrict: 'E',
    scope: {
      dfAnimated: '='
    },
    templateUrl: 'templates/directives/df-esfinge.html'
  }
});
