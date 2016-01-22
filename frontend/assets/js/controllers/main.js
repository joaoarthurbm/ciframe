angular.module('deciframeApp').controller('MainController', function($scope, $route) {

  $scope.isActive = function(path) {
  	if ($route.current && $route.current.regexp) {
  		return $route.current && $route.current.regexp.test(path);
  	}
  	return false;
  };

});
