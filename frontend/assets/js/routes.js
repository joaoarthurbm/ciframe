angular.module('deciframeApp').config(function($routeProvider) {
  $routeProvider
    .when('/', {
      templateUrl: "templates/home.html",
      controller: "HomeController"
    })
    .when('/sobre', {
      templateUrl: "templates/about.html",
      controller: "AboutController"
    })
    .otherwise({
      redirectTo: '/'
    });
});
