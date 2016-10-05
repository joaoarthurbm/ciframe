angular.module('deciframeApp').controller('MainController', function($scope, $route) {
  $scope.showMenu = false;
  $scope.isActive = function(path) {
  	if ($route.current && $route.current.regexp) {
  		return $route.current && $route.current.regexp.test(path);
  	}
  	return false;
  };
  $scope.toggleMenu = function() {
    $scope.showMenu = !$scope.showMenu;
  };
});
