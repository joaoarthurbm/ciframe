angular.module('deciframeApp').controller('SequenciaController', function($scope, $http) {
  // var sequenciasFamosas = ['Bm - G - D - A', "C - G - Am - F", "Em - G", "C - A7 - Dm - G7", "Gm - F", "C - C7 - F - Fm"];
  var sequencia1 = {
    'index': 1,
    'acordes': [
      { 'acorde': 'Bm', 'cor': '#2E1C74' },
      { 'acorde': 'G',  'cor': '#2E1C74' },
      { 'acorde': 'D',  'cor': '#2E1C74' },
      { 'acorde': 'A',  'cor': '#2E1C74' }
  ]};
  var sequencia2 = {
    'index': 1,
    'acordes': [
      { 'acorde': 'C',  'cor': '#2E1C74' },
      { 'acorde': 'G',  'cor': '#2E1C74' },
      { 'acorde': 'Am', 'cor': '#2E1C74' },
      { 'acorde': 'F',  'cor': '#2E1C74' }
  ]};
  var sequencia3 = {
    'index': 1,
    'acordes': [
      { 'acorde': 'Gm', 'cor': '#2E1C74' },
      { 'acorde': 'F',  'cor': '#2E1C74' }
  ]};
  var sequencia4 = {
    'index': 1,
    'acordes': [
      { 'acorde': 'C',  'cor': '#2E1C74' },
      { 'acorde': 'C7', 'cor': '#2E1C74' },
      { 'acorde': 'F',  'cor': '#2E1C74' },
      { 'acorde': 'Fm', 'cor': '#2E1C74' }
  ]};
  $scope.sequenciasFamosas = [];
  $scope.sequenciasFamosas.push(sequencia1);
  $scope.sequenciasFamosas.push(sequencia2);
  $scope.sequenciasFamosas.push(sequencia3);
  $scope.sequenciasFamosas.push(sequencia4);
  $scope.minhaSequencia = {};
  $scope.isSearching = false;
  $scope.musicas = [];

  $scope.addSequencia = function(sequencia) {
    $scope.minhaSequencia = sequencia
    $scope.pesquisarPorSequencia();
  }
  $scope.pesquisarPorSequencia = function() {
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
