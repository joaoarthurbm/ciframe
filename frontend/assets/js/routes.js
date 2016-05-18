angular.module('deciframeApp').config(function($routeProvider) {
  $routeProvider
    .when('/', {
      templateUrl: "templates/home.html",
      controller: "HomeController"
    })
    .when('/poracordes', {
      templateUrl: "templates/acordes.html",
      controller: "AcordesController"
    })
    .when('/pormusica', {
      templateUrl: "templates/musica.html",
      controller: "SearchController"
    })
    .when('/porsequencia', {
      templateUrl: "templates/sequencia.html",
      controller: "SequenciaController"
    })
    .when('/sobre', {
      templateUrl: "templates/about.html",
      controller: "AboutController"
    })
    .otherwise({
      redirectTo: '/'
    });
});
