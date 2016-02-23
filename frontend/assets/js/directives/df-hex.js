angular.module('deciframeApp').directive('dfHex', function() {
  return {
    restrict: 'E',
    templateUrl: 'templates/directives/df-hex.html',
    link: function(scope, element, attrs) {
      scope.acorde = attrs.acorde;
      scope.acordeColor = attrs.acordeColor;
    }
  }
});
