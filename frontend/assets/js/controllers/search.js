angular.module('deciframeApp').controller('SearchController', function($scope, $http) {
  $scope.isSearching = false;
  $scope.tituloMusica = '';
  $scope.musicas = [];

  $scope.pesquisarPorTitulo = function() {
    $scope.isSearching = true;
    // Developing only >>>
    $scope.musicas.push(
      {
        "titulo": "Californication "+$scope.musicas.length,
        "artista": "Red Hot Chili Peppers",
        "link": "http://www.cifraclub.com.br/red-hot-chili-peppers/californication/"
      }
    );
    // Remove later <<<<
    $http.get("")
    .success(function(data) {
      // $scope.musicas = data;
      $scope.isSearching = false;
    })
    .error(function(data) {
      $scope.isSearching = false;
    });
  }
});
