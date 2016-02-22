angular.module('deciframeApp').config(function($routeProvider) {
  $routeProvider
    .when('/', {
      templateUrl: "templates/home.html",
      controller: "HomeController"
    })
    .when('/poracordes', {
      templateUrl: "templates/acordes.html",
      controller: "AboutController"
    })
    .when('/pormusica', {
      templateUrl: "templates/musica.html",
      controller: "AboutController"
    })
    .when('/porsequencia', {
      templateUrl: "templates/sequencia.html",
      controller: "AboutController"
    })
    .when('/sobre', {
      templateUrl: "templates/about.html",
      controller: "AboutController"
    })
    .otherwise({
      redirectTo: '/'
    });
});
