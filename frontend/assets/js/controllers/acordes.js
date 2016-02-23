angular.module('deciframeApp').controller('AcordesController', function($scope, $http) {
  var acordesC = [
    { 'acorde': 'C',  'cor': '#e6b300' },
    { 'acorde': 'C#', 'cor': '#e6b300' },
    { 'acorde': 'Cm', 'cor': '#efcc59' },
    { 'acorde': 'C#m','cor': '#efcc59' },
    { 'acorde': 'C7', 'cor': '#d6a602' },
    { 'acorde': 'C#7','cor': '#d6a602' }];
  var acordesD = [
    { 'acorde': 'D',  'cor': '#cb6018' },
    { 'acorde': 'D#', 'cor': '#cb6018' },
    { 'acorde': 'Dm', 'cor': '#cf6f3e' },
    { 'acorde': 'D#m','cor': '#cf6f3e' },
    { 'acorde': 'D7', 'cor': '#bc5a1d' },
    { 'acorde': 'D#7','cor': '#bc5a1d' }];
  var acordesE = [
    { 'acorde': 'E',  'cor': '#b72c52' },
    { 'acorde': 'Em', 'cor': '#c5516e' },
    { 'acorde': 'E7', 'cor': '#a92f4d' }];
  var acordesF = [
    { 'acorde': 'F',  'cor': '#ba007c' },
    { 'acorde': 'F#', 'cor': '#ba007c' },
    { 'acorde': 'Fm', 'cor': '#c02a88' },
    { 'acorde': 'F#m','cor': '#c02a88' },
    { 'acorde': 'F7', 'cor': '#ad0076' },
    { 'acorde': 'F#7','cor': '#ad0076' }];
  var acordesG = [
    { 'acorde': 'G',  'cor': '#7b057e' },
    { 'acorde': 'G#', 'cor': '#7b057e' },
    { 'acorde': 'Gm', 'cor': '#882888' },
    { 'acorde': 'G#m','cor': '#882888' },
    { 'acorde': 'G7', 'cor': '#710c77' },
    { 'acorde': 'G#7','cor': '#710c77' }];
  var acordesA = [
    { 'acorde': 'A',  'cor': '#76aadb' },
    { 'acorde': 'A#', 'cor': '#76aadb' },
    { 'acorde': 'Am', 'cor': '#89c0e9' },
    { 'acorde': 'A#m','cor': '#89c0e9' },
    { 'acorde': 'A7', 'cor': '#6c9ecc' },
    { 'acorde': 'A#7','cor': '#6c9ecc' }];
  var acordesB = [
    { 'acorde': 'B',  'cor': '#a3bd31' },
    { 'acorde': 'Bm', 'cor': '#cdd54f' },
    { 'acorde': 'B7', 'cor': '#96b02f' }];
  $scope.acordes = [];
  $scope.acordes.push(acordesC);
  $scope.acordes.push(acordesD);
  $scope.acordes.push(acordesE);
  $scope.acordes.push(acordesF);
  $scope.acordes.push(acordesG);
  $scope.acordes.push(acordesA);
  $scope.acordes.push(acordesB);
  $scope.meusAcordes = [];
  $scope.isSearching = false;
  $scope.musicas = [];

  $scope.addAcorde = function(acorde) {
    console.log(acorde);
    if ($scope.meusAcordes.indexOf(acorde) == -1) {
      $scope.meusAcordes.push(acorde);
    } else {
      var index = $scope.meusAcordes.indexOf(acorde);
      if (index > -1) $scope.meusAcordes.splice(index, 1);
    }
    $scope.pesquisarPorAcordes();
  }
  $scope.temAcorde = function(acorde) {
    return ($scope.meusAcordes.indexOf(acorde) > -1);
  }
  $scope.pesquisarPorAcordes = function() {
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
