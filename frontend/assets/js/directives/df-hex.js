angular.module('deciframeApp').directive('dfHex', function() {
  return {
    restrict: 'E',
    templateUrl: 'templates/directives/df-hex.html',
    scope: {},
    link: function(scope, element, attrs) {
      scope.acorde = attrs.acorde;
      scope.acordeColor = attrs.acordeColor;
    }
  }
});
